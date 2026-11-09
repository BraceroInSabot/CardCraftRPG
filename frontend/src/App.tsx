import { Button, Stack, Text, Title } from '@mantine/core'
import { Link, Route, Routes, useParams } from 'react-router-dom'
import { EntityPage } from './components/entity/EntityPage'
import { AppLayout } from './components/layout/AppLayout'
import { HomePage } from './pages/HomePage'
import { findResource } from './resources/definitions'

function ResourceRoute() {
  const { resourceKey } = useParams()
  const resource = findResource(resourceKey)
  if (!resource) return <NotFound />
  // Keyed so selection and dialogs reset when switching resources.
  return <EntityPage key={resource.key} resource={resource} />
}

function NotFound() {
  return (
    <Stack align="flex-start">
      <Title order={2}>This page does not exist</Title>
      <Text c="dimmed">Pick a section in the menu, or go back to the start.</Text>
      <Button component={Link} to="/" variant="light">
        Go to getting started
      </Button>
    </Stack>
  )
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path=":resourceKey" element={<ResourceRoute />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
