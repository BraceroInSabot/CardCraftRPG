import { Button, ColorInput, Group, Paper, PasswordInput, SimpleGrid, Stack, Text, TextInput, Title } from '@mantine/core'
import { useForm, type UseFormReturnType } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { accountApi, type PasswordChange, type ProfileChanges } from '../api/accountApi'
import { ApiError } from '../api/http'
import { ME_QUERY_KEY, useAuth } from '../auth/useAuth'
import { BACKGROUND_SWATCHES, type Master } from '../domain/types'

/** Show field errors from the API on the form, anything else as a notification. */
function reportError<T>(form: UseFormReturnType<T>, error: Error) {
  if (error instanceof ApiError && Object.keys(error.fieldErrors).length > 0) {
    form.setErrors(Object.fromEntries(Object.entries(error.fieldErrors).map(([key, msgs]) => [key, msgs.join(' ')])))
    return
  }
  notifications.show({ color: 'red', title: 'Not saved', message: error.message })
}

function Section({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <Paper withBorder radius="md" p="lg">
      <Stack gap="sm">
        <div>
          <Title order={4}>{title}</Title>
          <Text size="sm" c="dimmed">
            {description}
          </Text>
        </div>
        {children}
      </Stack>
    </Paper>
  )
}

function useSaveMaster() {
  const queryClient = useQueryClient()
  return (master: Master, message: string) => {
    queryClient.setQueryData(ME_QUERY_KEY, master)
    notifications.show({ color: 'teal', message })
  }
}

function ProfileForm({ master }: { master: Master }) {
  const saved = useSaveMaster()
  const form = useForm<Required<ProfileChanges>>({
    initialValues: { display_name: master.display_name, email: master.email },
  })
  const save = useMutation({
    mutationFn: accountApi.updateProfile,
    onSuccess: (updated) => {
      form.resetDirty({ display_name: updated.display_name, email: updated.email })
      saved(updated, 'Profile saved.')
    },
    onError: (error) => reportError(form, error),
  })
  return (
    <Section title="Profile" description="How you appear in Card Craft.">
      <form onSubmit={form.onSubmit((values) => save.mutate(values))}>
        <Stack gap="sm">
          <TextInput label="Username" value={master.username} disabled description="Used to sign in." />
          <TextInput label="Display name" maxLength={120} {...form.getInputProps('display_name')} />
          <TextInput label="Email" type="email" autoComplete="email" {...form.getInputProps('email')} />
          <Group justify="flex-end">
            <Button type="submit" loading={save.isPending} disabled={!form.isDirty()}>
              Save profile
            </Button>
          </Group>
        </Stack>
      </form>
    </Section>
  )
}

function CardDefaultsForm({ master }: { master: Master }) {
  const saved = useSaveMaster()
  const form = useForm({
    initialValues: { default_background_color: master.default_background_color },
    validate: {
      default_background_color: (value) => (/^#[0-9a-f]{6}$/i.test(value) ? null : 'Use a hex color such as #ffffff.'),
    },
  })
  const save = useMutation({
    mutationFn: (color: string) => accountApi.updateCardDefaults(color.toLowerCase()),
    onSuccess: (updated) => {
      form.resetDirty({ default_background_color: updated.default_background_color })
      saved(updated, 'Card defaults saved.')
    },
    onError: (error) => reportError(form, error),
  })
  return (
    <Section title="Card defaults" description="Preselected when you create a new card. Existing cards keep their look.">
      <form onSubmit={form.onSubmit((values) => save.mutate(values.default_background_color))}>
        <Stack gap="sm">
          <ColorInput
            label="Background color"
            format="hex"
            swatches={BACKGROUND_SWATCHES}
            swatchesPerRow={9}
            withEyeDropper={false}
            {...form.getInputProps('default_background_color')}
          />
          <Group justify="flex-end">
            <Button type="submit" loading={save.isPending} disabled={!form.isDirty()}>
              Save defaults
            </Button>
          </Group>
        </Stack>
      </form>
    </Section>
  )
}

function PasswordForm() {
  const form = useForm<PasswordChange & { confirm: string }>({
    initialValues: { current_password: '', new_password: '', confirm: '' },
    validate: {
      current_password: (value) => (value ? null : 'Enter your current password.'),
      new_password: (value) => (value.length >= 8 ? null : 'Use at least 8 characters.'),
      confirm: (value, values) => (value === values.new_password ? null : 'The passwords do not match.'),
    },
  })
  const save = useMutation({
    mutationFn: ({ current_password, new_password }: PasswordChange) =>
      accountApi.changePassword({ current_password, new_password }),
    onSuccess: () => {
      form.reset()
      notifications.show({ color: 'teal', message: 'Password changed. Other devices were signed out.' })
    },
    onError: (error) => reportError(form, error),
  })
  return (
    <Section title="Password" description="Your current password is required to set a new one.">
      <form onSubmit={form.onSubmit((values) => save.mutate(values))}>
        <Stack gap="sm">
          <PasswordInput
            label="Current password"
            autoComplete="current-password"
            {...form.getInputProps('current_password')}
          />
          <PasswordInput label="New password" autoComplete="new-password" {...form.getInputProps('new_password')} />
          <PasswordInput label="Repeat the new password" autoComplete="new-password" {...form.getInputProps('confirm')} />
          <Group justify="flex-end">
            <Button type="submit" loading={save.isPending}>
              Change password
            </Button>
          </Group>
        </Stack>
      </form>
    </Section>
  )
}

export function SettingsPage() {
  const { master } = useAuth()
  if (!master) return null
  return (
    <Stack maw={980}>
      <Title order={2}>Settings</Title>
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <Stack>
          <ProfileForm master={master} />
          <CardDefaultsForm master={master} />
        </Stack>
        <PasswordForm />
      </SimpleGrid>
    </Stack>
  )
}
