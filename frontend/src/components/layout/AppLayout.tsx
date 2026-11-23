import { AppShell, Avatar, Burger, Group, Menu, NavLink, ScrollArea, Text, Title, UnstyledButton } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { notifications } from '@mantine/notifications'
import { IconChevronDown, IconHome2, IconLogout, IconSettings } from '@tabler/icons-react'
import { useMutation } from '@tanstack/react-query'
import { NavLink as RouterLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { accountApi } from '../../api/accountApi'
import { useAuth } from '../../auth/useAuth'
import { CARD_RESOURCE_KEYS, resources } from '../../resources/definitions'
import type { ResourceDefinition } from '../../resources/types'

const groups: { title: string; keys: string[] }[] = [
  { title: 'Cards', keys: CARD_RESOURCE_KEYS },
  { title: 'Setting', keys: ['systems', 'campaigns'] },
]

function UserMenu() {
  const { master, reset } = useAuth()
  const navigate = useNavigate()
  const logout = useMutation({
    mutationFn: accountApi.logout,
    onSuccess: () => {
      reset(null)
      navigate('/login', { replace: true })
    },
    onError: (error) => notifications.show({ color: 'red', title: 'Could not sign out', message: error.message }),
  })
  if (!master) return null
  const name = master.display_name || master.username

  return (
    <Menu position="bottom-end" width={200}>
      <Menu.Target>
        <UnstyledButton aria-label="Account menu">
          <Group gap={8}>
            <Avatar size={30} radius="xl" color="grape">
              {name.slice(0, 1).toUpperCase()}
            </Avatar>
            <Text size="sm" fw={600} visibleFrom="xs">
              {name}
            </Text>
            <IconChevronDown size={14} />
          </Group>
        </UnstyledButton>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Item component={RouterLink} to="/settings" leftSection={<IconSettings size={16} />}>
          Settings
        </Menu.Item>
        <Menu.Item color="red" leftSection={<IconLogout size={16} />} onClick={() => logout.mutate()}>
          Sign out
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}

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
          <Group ml="auto">
            <UserMenu />
          </Group>
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
