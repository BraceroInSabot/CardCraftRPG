import { Button, Grid, Group, Modal, NumberInput, Select, Stack, Text, TextInput, Textarea } from '@mantine/core'
import { useForm, type GetInputPropsReturnType } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useEffectEvent } from 'react'
import { ApiError } from '../../api/http'
import { DEFAULT_BACKGROUND, type BaseEntity } from '../../domain/types'
import { useLookups, type Lookups } from '../../hooks/useLookups'
import { cardFor } from '../../resources/cards'
import type { FieldDef, ResourceDefinition } from '../../resources/types'
import { GameCard } from '../cards/GameCard'
import { useImageDraft } from '../../hooks/useImageDraft'
import { CardAppearanceFields } from './CardAppearanceFields'

type FormValues = Record<string, string | number | null>

function initialValues(fields: FieldDef[], entity: BaseEntity | null, defaults: FormValues): FormValues {
  const source = (entity ?? {}) as unknown as Record<string, unknown>
  const values: FormValues = {}
  for (const field of fields) {
    const raw = entity ? source[field.name] : defaults[field.name]
    switch (field.kind) {
      case 'reference':
        values[field.name] = raw == null ? null : String(raw)
        break
      case 'number':
        values[field.name] = typeof raw === 'number' ? raw : ''
        break
      case 'choice':
        values[field.name] = (raw as string | undefined) ?? field.choices[0].value
        break
      default:
        values[field.name] = (raw as string | undefined) ?? ''
    }
  }
  return values
}

function toPayload(fields: FieldDef[], values: FormValues): Record<string, unknown> {
  const payload: Record<string, unknown> = {}
  for (const field of fields) {
    const value = values[field.name]
    if (field.kind === 'reference') payload[field.name] = value ? Number(value) : null
    else if (field.kind === 'number') payload[field.name] = value === '' || value === null ? null : Number(value)
    else payload[field.name] = value
  }
  return payload
}

function scopedOptions(field: Extract<FieldDef, { kind: 'reference' }>, lookups: Lookups, values: FormValues) {
  const options = lookups.options[field.lookup]
  if (!field.scopedBy) return options
  const scope = values[field.scopedBy]
  return scope ? options.filter((option) => option.systemId === Number(scope)) : []
}

interface Props {
  resource: ResourceDefinition
  /** `null` while closed, `'new'` to create, or the entity to edit. */
  target: BaseEntity | 'new' | null
  defaults: FormValues
  onClose(): void
}

export function EntityFormModal({ resource, target, defaults, onClose }: Props) {
  const opened = target !== null
  const editing = target !== null && target !== 'new' ? target : null
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={editing ? `Edit ${resource.singular}` : `New ${resource.singular}`}
      size={960}
      centered
    >
      {opened && (
        <EntityForm
          key={editing?.id ?? 'new'}
          resource={resource}
          entity={editing}
          defaults={defaults}
          onDone={onClose}
        />
      )}
    </Modal>
  )
}

function EntityForm({
  resource,
  entity,
  defaults,
  onDone,
}: {
  resource: ResourceDefinition
  entity: BaseEntity | null
  defaults: FormValues
  onDone(): void
}) {
  const lookups = useLookups()
  const queryClient = useQueryClient()
  const image = useImageDraft(entity?.image_url ?? null)
  const form = useForm<FormValues>({
    initialValues: {
      ...initialValues(resource.fields, entity, defaults),
      background_color: entity?.background_color ?? DEFAULT_BACKGROUND,
    },
    validate: (values) => {
      const errors: Record<string, string> = {}
      for (const field of resource.fields) {
        const value = values[field.name]
        if (field.required && (value === null || value === '' || (typeof value === 'string' && !value.trim()))) {
          errors[field.name] = `${field.label} is required.`
        }
      }
      if (!/^#[0-9a-f]{6}$/i.test(String(values.background_color ?? ''))) {
        errors.background_color = 'Use a hex color such as #ffffff.'
      }
      return errors
    },
  })

  // Clear scoped references (e.g. campaign) when their scope (system) changes.
  const scopeSignature = resource.fields
    .filter((field) => field.kind === 'reference' && field.scopedBy)
    .map((field) => (field.kind === 'reference' && field.scopedBy ? form.values[field.scopedBy] : ''))
    .join('|')
  const clearOutOfScope = useEffectEvent(() => {
    for (const field of resource.fields) {
      if (field.kind !== 'reference' || !field.scopedBy) continue
      const current = form.values[field.name]
      if (current && !scopedOptions(field, lookups, form.values).some((option) => option.value === current)) {
        form.setFieldValue(field.name, null)
      }
    }
  })
  useEffect(() => clearOutOfScope(), [scopeSignature, lookups.loading])

  const payloadOf = (values: FormValues) => ({
    ...toPayload(resource.fields, values),
    background_color: String(values.background_color).toLowerCase(),
  })

  const save = useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      const saved = entity ? await resource.api.update(entity.id, payload) : await resource.api.create(payload)
      // The card is saved first: the image endpoint needs its id.
      try {
        if (image.file) return { saved: await resource.api.uploadImage(saved.id, image.file), imageError: null }
        if (image.removed && entity?.image_url) return { saved: await resource.api.removeImage(saved.id), imageError: null }
      } catch (error) {
        return { saved, imageError: error as Error }
      }
      return { saved, imageError: null }
    },
    onSuccess: ({ saved, imageError }) => {
      queryClient.invalidateQueries()
      if (imageError) {
        notifications.show({
          color: 'yellow',
          title: `${saved.name} ${entity ? 'saved' : 'created'} without the new image`,
          message: imageError.message,
        })
      } else {
        notifications.show({ color: 'teal', message: `${saved.name} ${entity ? 'saved' : 'created'}.` })
      }
      onDone()
    },
    onError: (error) => {
      if (error instanceof ApiError && Object.keys(error.fieldErrors).length > 0) {
        const known = new Set([...resource.fields.map((field) => field.name), 'background_color'])
        const fieldErrors = Object.fromEntries(
          Object.entries(error.fieldErrors)
            .filter(([name]) => known.has(name))
            .map(([name, messages]) => [name, messages.join(' ')]),
        )
        form.setErrors(fieldErrors)
        const unknown = Object.entries(error.fieldErrors).filter(([name]) => !known.has(name))
        if (unknown.length === 0) return
        notifications.show({ color: 'red', title: 'Not saved', message: unknown.map(([, m]) => m.join(' ')).join(' ') })
        return
      }
      notifications.show({ color: 'red', title: 'Not saved', message: (error as Error).message })
    },
  })

  const previewEntity = {
    ...(entity ?? {}),
    ...payloadOf(form.values),
    id: entity?.id ?? 0,
    name: String(form.values.name ?? '').trim() || `New ${resource.singular}`,
    image_url: image.previewUrl,
  } as unknown as BaseEntity

  return (
    <form onSubmit={form.onSubmit((values) => save.mutate(payloadOf(values)))}>
      <Grid gap="xl">
        <Grid.Col span={{ base: 12, sm: 7 }}>
          <Stack gap="sm">
            {resource.fields.map((field) => renderField(field, form, lookups, entity))}
            <CardAppearanceFields
              colorProps={form.getInputProps('background_color')}
              image={image}
            />
          </Stack>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 5 }}>
          <Stack gap={6} align="center" pos="sticky" top={72}>
            <Text size="sm" fw={600} c="dimmed">
              Preview
            </Text>
            <GameCard card={cardFor(resource, previewEntity, lookups)} />
          </Stack>
        </Grid.Col>
      </Grid>
      <Group justify="flex-end" mt="lg">
        <Button variant="default" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" loading={save.isPending}>
          {entity ? 'Save changes' : `Create ${resource.singular}`}
        </Button>
      </Group>
    </form>
  )
}

function renderField(
  field: FieldDef,
  form: { values: FormValues; getInputProps(path: string): GetInputPropsReturnType },
  lookups: Lookups,
  entity: BaseEntity | null,
) {
  const common = {
    label: field.label,
    description: field.description,
    withAsterisk: field.required,
  }
  switch (field.kind) {
    case 'text':
      return (
        <TextInput
          key={field.name}
          {...common}
          {...form.getInputProps(field.name)}
          maxLength={field.maxLength}
          placeholder={field.placeholder}
          data-autofocus={field.name === 'name' || undefined}
        />
      )
    case 'textarea':
      return (
        <Textarea
          key={field.name}
          {...common}
          {...form.getInputProps(field.name)}
          maxLength={field.maxLength}
          autosize
          minRows={4}
          maxRows={10}
        />
      )
    case 'number':
      return (
        <NumberInput
          key={field.name}
          {...common}
          {...form.getInputProps(field.name)}
          min={field.min}
          max={field.max}
          allowDecimal={false}
          placeholder={field.placeholder}
        />
      )
    case 'choice':
      return (
        <Select
          key={field.name}
          {...common}
          {...form.getInputProps(field.name)}
          data={field.choices.map(({ value, label }) => ({ value, label }))}
          allowDeselect={false}
        />
      )
    case 'reference': {
      const options = scopedOptions(field, lookups, form.values)
      const waitingForScope = Boolean(field.scopedBy && !form.values[field.scopedBy])
      return (
        <Select
          key={field.name}
          {...common}
          {...form.getInputProps(field.name)}
          data={options.map(({ value, label }) => ({ value, label }))}
          searchable
          clearable={!field.required}
          disabled={(field.lockedOnEdit && entity !== null) || waitingForScope}
          placeholder={waitingForScope ? 'Choose a system first' : options.length ? 'Choose one' : 'Nothing to choose yet'}
          nothingFoundMessage="No match"
        />
      )
    }
  }
}
