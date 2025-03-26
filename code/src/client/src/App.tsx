import React from 'react';
import { 
  AppShell, 
  Burger, 
  NavLink, 
  Group, 
  Title, 
  Text, 
  Flex, 
  Box, 
  useMantineTheme, 
  rem,
  Paper,
  ThemeIcon,
  Badge,
  Transition,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Notifications } from '@mantine/notifications';
import { BrowserRouter as Router, Route, Routes, Link, useLocation } from 'react-router-dom';
import {
  IconFileUpload, 
  IconUpload,
  IconHistory,
  IconShieldLock,
  IconDashboard,
} from '@tabler/icons-react';

// Import your components
import Dashboard from './components/Dashboard';
import TransactionForm from './components/TransactionForm';
import TransactionResults from './components/TransactionResults';
import TransactionHistory from './components/TransactionHistory';
import BulkTransactionUpload from './components/BulkTransactionUpload';

// Define the structure for navigation links
interface NavItem {
  icon: React.ReactNode;
  label: string;
  to: string;
  description?: string;
  badge?: string;
  badgeColor?: string;
  children?: NavItem[];
}

function NavBarLink({ icon, label, to, description, badge, badgeColor = 'blue', active = false }: 
  { icon: React.ReactNode; label: string; to: string; description?: string; badge?: string; badgeColor?: string; active?: boolean }) {
  const theme = useMantineTheme();
  
  return (
    <NavLink
      component={Link}
      to={to}
      label={
        <Flex justify="space-between" align="center" w="100%">
          <Box>
            <Text fw={500} size="sm">{label}</Text>
            {description && (
              <Text size="xs" c="dimmed" lineClamp={1}>
                {description}
              </Text>
            )}
          </Box>
          {badge && (
            <Badge size="sm" color={badgeColor} variant="filled">
              {badge}
            </Badge>
          )}
        </Flex>
      }
      leftSection={
        <ThemeIcon 
          size={30} 
          variant={active ? "filled" : "light"} 
          color={active ? theme.primaryColor : "gray"}
          style={{ 
            transition: 'all 0.2s ease',
            borderRadius: theme.radius.md,
            opacity: active ? 1 : 0.7
          }}
        >
          {icon}
        </ThemeIcon>
      }
      active={active}
      style={(theme) => ({
        borderRadius: theme.radius.md,
        transition: 'all 0.2s ease',
        marginBottom: rem(4),
      })}
    />
  );
}

// Active route component to determine which link is active
function AppRoutes() {
  
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/submit" element={<TransactionForm />} />
      <Route path="/results/:transactionId" element={<TransactionResults />} />
      <Route path="/bulk-upload" element={<BulkTransactionUpload />} />
      <Route path="/history" element={<TransactionHistory />} />
    </Routes>
  );
}

// RouterNavigation component with expanded features
function RouterNavigation() {
  const location = useLocation();
  const currentPath = location.pathname;
  // Define main navigation items
  const mainNavItems: NavItem[] = [
    {
      icon: <IconDashboard size={18} />,
      label: 'Dashboard',
      to: '/',
      description: 'Overview & statistics'
    },
    {
      icon: <IconUpload size={18} />,
      label: 'Bulk Upload',
      to: '/bulk-upload',
      description: 'Process multiple transactions',
      badge: 'New'
    },
    {
      icon: <IconFileUpload size={18} />,
      label: 'Submit Transaction',
      to: '/submit',
      description: 'Create new assessment'
    },
    {
      icon: <IconHistory size={18} />,
      label: 'Transaction History',
      to: '/history',
      description: 'View past assessments'
    }
  ];
  
  
  return (
    <Flex direction="column" justify="space-between" h="100%">
      <Flex justify="space-between" align="center" mb={rem(10)}>
        <Title order={5} ml={rem(12)}>Navigation</Title>
      </Flex>

      <Box mb={rem(30)}>
        {mainNavItems.map((item) => (
          <NavBarLink
            key={item.to}
            icon={item.icon}
            label={item.label}
            to={item.to}
            description={item.description}
            badge={item.badge}
            badgeColor={item.badgeColor}
            active={currentPath === item.to}
          />
        ))}
      </Box>

      <Box mt="auto" mb={rem(20)}>
        <Paper 
          withBorder
          p="sm" 
          radius="md" 
          bg="rgba(0, 0, 0, 0.03)" 
          style={{
            backdropFilter: 'blur(7px)',
            margin: `0 ${rem(10)}`
          }}
        >
          <Flex gap="md" align="center">
            <ThemeIcon size="lg" radius="md" color="blue" variant="light">
              <IconShieldLock size={20} />
            </ThemeIcon>
            
            <Transition mounted={true} transition="slide-right" duration={200} timingFunction="ease">
              {(styles) => (
                <Box style={styles}>
                  <Text size="xs" fw={500}>EIRA</Text>
                  <Text size="xs" c="dimmed">v1.0.0</Text>
                </Box>
              )}
            </Transition>
          </Flex>
        </Paper>
      </Box>
    </Flex>
  );
}

const App: React.FC = () => {
  const [opened, { toggle }] = useDisclosure();
  const theme = useMantineTheme();

  return (
    <Router>
      <Notifications position="top-right" />
      <AppShell
        header={{ height: 60 }}
        navbar={{
          width: 280,
          breakpoint: 'sm',
          collapsed: { mobile: !opened }
        }}
        padding="md"
      >
        <AppShell.Header style={{ 
          backdropFilter: 'blur(10px)',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          borderBottom: `1px solid ${theme.colors.gray[2]}`,
        }}>
          <Group h="100%" px="md" justify="space-between">
            <Group>
              <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
              <Group>
                <ThemeIcon size={34} radius="md" variant="gradient" gradient={{ from: 'blue', to: 'cyan', deg: 90 }}>
                  <IconShieldLock size={20} />
                </ThemeIcon>
                <Box>
                  <Title order={3} size="h4">Entity Risk Assessment</Title>
                </Box>
              </Group>
            </Group>
          </Group>
        </AppShell.Header>

        <AppShell.Navbar 
          p="md" 
          style={{ 
            backdropFilter: 'blur(10px)',
            backgroundColor: 'rgba(255, 255, 255, 0.7)',
            borderRight: `1px solid ${theme.colors.gray[2]}`,
          }}
        >
            <RouterNavigation />
        </AppShell.Navbar>

        <AppShell.Main 
          style={{ 
            backgroundColor: theme.colors.gray[0],
            // padding: rem(20)
          }}
        >
          <Paper
            p="md"
            radius="lg"
            shadow="sm"
            style={{
              minHeight: 'calc(100vh - 100px)'
            }}
          >
            <AppRoutes />
          </Paper>
        </AppShell.Main>
      </AppShell>
    </Router>
  );
};

export default App;