import { AppShell, Burger, Group, NavLink, ScrollArea, Text, Title } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconHome2 } from '@tabler/icons-react'
import { NavLink as RouterLink, Outlet, useLocation } from 'react-router-dom'
import { CARD_RESOURCE_KEYS, resources } from '../../resources/definitions'
import type { ResourceDefinition } from '../../resources/types'

const groups: { title: string; keys: string[] }[] = [
  { title: 'Cards', keys: CARD_RESOURCE_KEYS },
  { title: 'Setting', keys: ['systems', 'campaigns'] },
]

export function AppLayout() {
  const [opened, { toggle, close }] = useDisclosure()
  const location = useLocation()

  const link = (resource: ResourceDefinition) => {
    const Icon = resource.icon
    return (
      <NavLink
        key={resource.key}
        component={RouterLink}
        to={`/${resource.key}`}
        label={resource.label}
        leftSection={<Icon size={18} stroke={1.75} color={resource.color} />}
        active={location.pathname === `/${resource.key}`}
        onClick={close}
        style={{ borderRadius: 8 }}
      />
    )
  }

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 240, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="lg"
    >
      <AppShell.Header>
        <Group h="100%" px="lg" gap="sm">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" aria-label="Toggle navigation" />
          <img src="/favicon.svg" width={28} height={28} alt="" />
          <Title order={3} ff="Alegreya, Georgia, serif" fw={800}>
            Card Craft RPG
          </Title>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="sm">
        <ScrollArea>
          <NavLink
            component={RouterLink}
            to="/"
            label="Getting started"
            leftSection={<IconHome2 size={18} stroke={1.75} />}
            active={location.pathname === '/'}
            onClick={close}
            style={{ borderRadius: 8 }}
          />
          {groups.map((group) => (
            <div key={group.title}>
              <Text size="xs" fw={700} c="dimmed" px="sm" mt="lg" mb={4}>
                {group.title}
              </Text>
              {group.keys.map((key) => {
                const resource = resources.find((candidate) => candidate.key === key)
                return resource ? link(resource) : null
              })}
            </div>
          ))}
        </ScrollArea>
      </AppShell.Navbar>

      <AppShell.Main bg="gray.0">
        <Outlet />
      </AppShell.Main>
    </AppShell>
  )
}
