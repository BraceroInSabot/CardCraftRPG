import { Button, ColorInput, FileInput, Group, Stack, Text } from '@mantine/core'
import { IconPhoto, IconTrash } from '@tabler/icons-react'
import type { GetInputPropsReturnType } from '@mantine/form'
import { BACKGROUND_SWATCHES, IMAGE_RULES } from '../../domain/types'
import type { ImageDraft } from '../../hooks/useImageDraft'

interface Props {
  colorProps: GetInputPropsReturnType
  image: ImageDraft
}

export function CardAppearanceFields({ colorProps, image }: Props) {
  const showRemove = image.previewUrl !== null

  return (
    <Stack gap="sm" mt="xs">
      <Text fw={700} size="sm">
        Card appearance
      </Text>
      <ColorInput
        label="Background color"
        description="Text turns light automatically on dark colors."
        format="hex"
        swatches={BACKGROUND_SWATCHES}
        swatchesPerRow={9}
        withEyeDropper={false}
        {...colorProps}
      />
      <Stack gap={6}>
        <FileInput
          label="Image"
          description="Shown below the title. PNG, JPEG, WebP or GIF, up to 5 MB."
          placeholder={image.previewUrl && !image.file ? 'Replace the current image' : 'Choose an image'}
          accept={IMAGE_RULES.accept}
          leftSection={<IconPhoto size={16} />}
          value={image.file}
          onChange={image.choose}
          error={image.error}
          clearable
        />
        {showRemove && (
          <Group>
            <Button
              variant="subtle"
              color="red"
              size="compact-sm"
              leftSection={<IconTrash size={14} />}
              onClick={image.remove}
            >
              Remove image
            </Button>
          </Group>
        )}
      </Stack>
    </Stack>
  )
}
