import { Alert, Button, Center, Paper, PasswordInput, Stack, Text, TextInput, Title } from '@mantine/core'
import { useForm } from '@mantine/form'
import { IconAlertCircle } from '@tabler/icons-react'
import { useMutation } from '@tanstack/react-query'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { accountApi, type Credentials } from '../api/accountApi'
import { ApiError } from '../api/http'
import { useAuth } from '../auth/useAuth'

const GENERIC_ERROR = 'Invalid username or password.'

function errorMessage(error: Error): string {
  if (error instanceof ApiError && error.status === 429) return 'Too many attempts. Wait a minute and try again.'
  if (error instanceof ApiError && error.status === 0) return error.message
  return GENERIC_ERROR
}

export function LoginPage() {
  const { master, reset } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from
  const destination = from && from !== '/login' ? from : '/'

  const form = useForm<Credentials>({
    initialValues: { username: '', password: '' },
    validate: {
      username: (value) => (value.trim() ? null : 'Enter your username.'),
      password: (value) => (value ? null : 'Enter your password.'),
    },
  })

  const login = useMutation({
    mutationFn: (credentials: Credentials) =>
      accountApi.login({ ...credentials, username: credentials.username.trim() }),
    onSuccess: (signedIn) => {
      reset(signedIn)
      navigate(destination, { replace: true })
    },
    onError: () => form.setFieldValue('password', ''),
  })

  if (master) return <Navigate to={destination} replace />

  return (
    <Center mih="100vh" bg="gray.0" p="md">
      <Paper withBorder radius="md" p="xl" w={380} shadow="sm">
        <form onSubmit={form.onSubmit((values) => login.mutate(values))}>
          <Stack>
            <Stack gap={4} align="center">
              <img src="/favicon.svg" width={40} height={40} alt="" />
              <Title order={2} ff="Alegreya, Georgia, serif" fw={800}>
                Card Craft RPG
              </Title>
              <Text size="sm" c="dimmed">
                Sign in to manage your cards.
              </Text>
            </Stack>
            {login.error && (
              <Alert color="red" icon={<IconAlertCircle size={18} />} role="alert">
                {errorMessage(login.error)}
              </Alert>
            )}
            <TextInput label="Username" autoComplete="username" data-autofocus {...form.getInputProps('username')} />
            <PasswordInput label="Password" autoComplete="current-password" {...form.getInputProps('password')} />
            <Button type="submit" loading={login.isPending} fullWidth>
              Sign in
            </Button>
          </Stack>
        </form>
      </Paper>
    </Center>
  )
}
