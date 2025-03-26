import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Table, Title, Badge, Button, Text, Card,
  TextInput, ActionIcon, Group, Flex, Menu, Pagination, Alert, ScrollArea,
  Center, ThemeIcon, Divider, Box, Paper, Collapse, Stack,
  SegmentedControl, Progress, MultiSelect, RingProgress, Tooltip,
  useMantineTheme, Grid
} from '@mantine/core';
import { useToggle, useHover, useMediaQuery } from '@mantine/hooks';
import {
  IconSearch, IconFilter, IconSortAscending, IconChevronDown,
  IconSortDescending, IconArrowRight, IconAlertCircle, IconEye, IconRefresh,
  IconCalendar, IconChartBar, IconFilterOff,
  IconChevronsDown, IconAdjustments, IconFileAnalytics,
  IconX, IconArrowsExchange,
  IconShield, IconShieldCheck, IconAlertTriangle, IconCircleCheck, IconBuildingSkyscraper
} from '@tabler/icons-react';

import { fetchTransactionHistory } from '../api/transactionApi';

interface Transaction {
  transaction_id: string;
  timestamp: string;
  status: 'completed' | 'processing' | 'failed';
  risk_score: number;
  entities_count: number;
}

// Helper function for date formatting
const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(date);
  } catch (e) {
    return dateString;
  }
};

// Helper function for risk color
const getRiskColor = (score: number) => {
  if (score >= 0.7) return 'red';
  if (score >= 0.4) return 'orange';
  return 'green';
};

// Helper function for risk label
const getRiskLabel = (score: number) => {
  if (score >= 0.7) return 'High Risk';
  if (score >= 0.4) return 'Medium Risk';
  return 'Low Risk';
};

// Status colors mapping
const statusColors: Record<string, string> = {
  'completed': 'green',
  'processing': 'blue',
  'failed': 'red'
};

// Enhanced transaction card component
const TransactionCard = ({ transaction, onView }: { transaction: Transaction, onView: () => void }) => {
  const theme = useMantineTheme();
  const { hovered, ref } = useHover();
  const risk = transaction.risk_score;
  const riskColor = getRiskColor(risk);

  return (
    <Paper
      ref={ref}
      withBorder
      p="md"
      radius="md"
      shadow={hovered ? "md" : "sm"}
      className="card-hover-effect"
      style={{
        transform: hovered ? 'translateY(-4px)' : 'translateY(0)',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      <Flex direction="column" h="100%">
        <Flex justify="space-between" align="flex-start" mb="xs">
          <Flex align="center" gap="xs">
            <ThemeIcon
              color={statusColors[transaction.status] || 'gray'}
              variant={hovered ? "filled" : "light"}
              size="lg"
              radius="md"
              style={{ transition: 'all 0.2s ease' }}
            >
              {transaction.status === 'completed' ? (
                <IconCircleCheck size={18} />
              ) : transaction.status === 'processing' ? (
                <IconArrowsExchange size={18} />
              ) : (
                <IconX size={18} />
              )}
            </ThemeIcon>

            <Box>
              <Text fw={600} size="sm" truncate>
                {transaction.transaction_id}
              </Text>
              <Flex align="center" gap={4}>
                <IconCalendar size={12} color={theme.colors.gray[6]} />
                <Text size="xs" c="dimmed">
                  {formatDate(transaction.timestamp)}
                </Text>
              </Flex>
            </Box>
          </Flex>

          <Badge color={riskColor} radius="sm" variant="filled" size="sm">
            {Math.round(risk * 100)}%
          </Badge>
        </Flex>

        <Flex align="center" gap="sm" mb="md">
          <RingProgress
            size={60}
            thickness={4}
            roundCaps
            sections={[{ value: risk * 100, color: riskColor }]}
            label={
              <Center>
                <ThemeIcon color={riskColor} variant="light" radius="xl" size="sm">
                  {risk >= 0.7 ? (
                    <IconAlertTriangle size={12} />
                  ) : risk >= 0.4 ? (
                    <IconShield size={12} />
                  ) : (
                    <IconShieldCheck size={12} />
                  )}
                </ThemeIcon>
              </Center>
            }
          />

          <Box style={{ flex: 1 }}>
            <Text size="xs" fw={500} mb={4}>Risk Profile</Text>
            <Progress
              value={risk * 100}
              color={riskColor}
              size="sm"
              radius="xl"
              striped={risk >= 0.7}
              animated={risk >= 0.7}
            />
            <Text size="xs" mt={4}>{getRiskLabel(risk)}</Text>
          </Box>
        </Flex>

        <Flex align="center" gap="xs" mb="xs">
          <ThemeIcon size="xs" radius="xl" color="blue" variant="light">
            <IconBuildingSkyscraper size={10} />
          </ThemeIcon>
          <Text size="xs">{transaction.entities_count} entities</Text>
        </Flex>

        <Divider my="sm" />

        <Group mt="auto" justify="apart">
          <Button
            variant="light"
            size="xs"
            onClick={onView}
            leftSection={<IconEye size={14} />}
            radius="md"
          >
            View
          </Button>
        </Group>
      </Flex>
    </Paper>
  );
};

// Enhanced filter panel component
interface FilterPanelProps {
  filters: Record<string, any>;
  setFilters: (filters: Record<string, any>) => void;
  onToggleFilters: () => void;
  showFilters: boolean;
}

const FilterPanel = ({
  filters,
  setFilters,
  onToggleFilters,
  showFilters
}: FilterPanelProps) => {

  const clearAllFilters = () => {
    setFilters({});
  };

  return (
    <Box>
      <Flex justify="space-between" align="center" mb="xs">
        <Text fw={500} size="sm">Advanced Filters</Text>
        <Group gap="xs">
          <Button
            size="xs"
            variant="subtle"
            color="gray"
            onClick={clearAllFilters}
            leftSection={<IconFilterOff size={14} />}
          >
            Clear All
          </Button>
          <ActionIcon
            variant="subtle"
            onClick={onToggleFilters}
          >
            <IconChevronsDown size={18} style={{
              transform: showFilters ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s ease'
            }} />
          </ActionIcon>
        </Group>
      </Flex>

      <Collapse in={showFilters}>
        <Card withBorder radius="md" padding="sm" mt="xs">
          <Grid>
            <Grid.Col span={12} m={6}>
              <Box mb="xs">
                <Text size="xs" fw={500} mb={4}>Status</Text>
                <MultiSelect
                  data={[
                    { value: 'completed', label: 'Completed' },
                    { value: 'processing', label: 'Processing' },
                    { value: 'failed', label: 'Failed' }
                  ]}
                  value={filters.status || []}
                  onChange={(value) => setFilters({ ...filters, status: value })}
                  placeholder="Any status"
                  clearable
                  size="xs"
                />
              </Box>
            </Grid.Col>

            <Grid.Col span={12}>
              <Box mb="xs">
                <Text size="xs" fw={500} mb={4}>Risk Level</Text>
                <MultiSelect
                  data={[
                    { value: 'high', label: 'High Risk' },
                    { value: 'medium', label: 'Medium Risk' },
                    { value: 'low', label: 'Low Risk' }
                  ]}
                  value={filters.risk || []}
                  onChange={(value) => setFilters({ ...filters, risk: value })}
                  placeholder="Any risk level"
                  clearable
                  size="xs"
                />
              </Box>
            </Grid.Col>
          </Grid>

          <Flex justify="flex-end" mt="md">
            <Button
              size="xs"
              variant="filled"
              color="blue"
              leftSection={<IconFilter size={14} />}
              onClick={() => onToggleFilters()}
            >
              Apply Filters
            </Button>
          </Flex>
        </Card>
      </Collapse>
    </Box>
  );
};

// Removed custom Grid component

// Empty state component
const EmptyState = ({ onSubmitNew }: { onSubmitNew: () => void }) => {
  return (
    <Center py="xl">
      <Stack align="center" gap="md">
        <ThemeIcon size={60} radius="xl" color="gray" variant="light">
          <IconSearch size={30} />
        </ThemeIcon>
        <Title order={3}>No transactions found</Title>
        <Text c="dimmed" maw={400}>
          There are no transactions matching your search criteria. Try adjusting your filters or submit a new transaction.
        </Text>
        <Group mt="md">
          <Button
            variant="outline"
            leftSection={<IconFilterOff size={16} />}
            onClick={() => window.location.reload()}
          >
            Clear Filters
          </Button>
          <Button
            variant="filled"
            leftSection={<IconFileAnalytics size={16} />}
            onClick={onSubmitNew}
          >
            Submit New Transaction
          </Button>
        </Group>
      </Stack>
    </Center>
  );
};

// Transaction history main component
const TransactionHistory = () => {
  const navigate = useNavigate();
  const theme = useMantineTheme();
  const isMobile = useMediaQuery(`(max-width: ${theme.breakpoints.sm})`);

  // State
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<any>({});
  const [sortBy, setSortBy] = useState<string>('timestamp');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'grid'>(isMobile ? 'grid' : 'table');
  const [showFilters, toggleFilters] = useToggle([false, true]);

  const ITEMS_PER_PAGE = 8;

  // Fetch data
  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      const response = await fetchTransactionHistory();
      setTransactions(response);
      setError(null);
    } catch (error) {
      console.error("Failed to fetch transaction history:", error);
      setError("Failed to load transaction history. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  // Event handlers
  const handleRefresh = () => {
    fetchTransactions();
  };

  const handleViewTransaction = (transactionId: string) => {
    navigate(`/results/${transactionId}`);
  };

  // Filter transactions
  let filteredTransactions = transactions.filter(transaction => {
    // Apply search filter
    if (search && !transaction.transaction_id.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }

    // Apply status filter
    if (filters.status && filters.status.length > 0) {
      if (!filters.status.includes(transaction.status)) {
        return false;
      }
    }

    // Apply risk filter
    if (filters.risk && filters.risk.length > 0) {
      const riskLevel = transaction.risk_score >= 0.7 ? 'high' :
        transaction.risk_score >= 0.4 ? 'medium' : 'low';
      if (!filters.risk.includes(riskLevel)) {
        return false;
      }
    }

    // Apply date filters
    if (filters.dateFrom) {
      const fromDate = new Date(filters.dateFrom);
      const txnDate = new Date(transaction.timestamp);
      if (txnDate < fromDate) {
        return false;
      }
    }

    if (filters.dateTo) {
      const toDate = new Date(filters.dateTo);
      toDate.setHours(23, 59, 59, 999); // End of day
      const txnDate = new Date(transaction.timestamp);
      if (txnDate > toDate) {
        return false;
      }
    }

    // Add more filters as needed

    return true;
  });

  // Sort transactions
  filteredTransactions = filteredTransactions.sort((a, b) => {
    if (sortBy === 'timestamp') {
      return sortOrder === 'asc'
        ? new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        : new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    }

    if (sortBy === 'risk_score') {
      return sortOrder === 'asc'
        ? a.risk_score - b.risk_score
        : b.risk_score - a.risk_score;
    }

    if (sortBy === 'entities_count') {
      return sortOrder === 'asc'
        ? a.entities_count - b.entities_count
        : b.entities_count - a.entities_count;
    }

    return 0;
  });

  // Paginate transactions
  const paginatedTransactions = filteredTransactions.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE
  );

  const totalPages = Math.ceil(filteredTransactions.length / ITEMS_PER_PAGE);

  const displayTransactions = paginatedTransactions;

  return (
    <Box p="md">
      <Card withBorder radius="lg" shadow="sm" p="xl" mb="lg" className="fade-in">
        <Flex justify="space-between" align="center" mb="xl">
          <Box>
            <Title order={2}
              style={{
                background: 'linear-gradient(90deg, #1a73e8, #174ea6)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
              mb={4}
            >
              Transaction History
            </Title>
            <Text c="dimmed" size="sm">
              View and manage all your risk assessment transactions
            </Text>
          </Box>

          <Group gap="sm">
            <Button
              variant="subtle"
              onClick={handleRefresh}
              leftSection={<IconRefresh size={18} />}
              loading={loading}
              radius="md"
            >
              Refresh
            </Button>

            <Button
              component={Link}
              to="/submit"
              rightSection={<IconArrowRight size={18} />}
              radius="md"
              variant="gradient"
              gradient={{ from: 'blue', to: 'cyan' }}
            >
              New Transaction
            </Button>
          </Group>
        </Flex>

        <Flex direction="column" gap="md">
          <Flex justify="space-between" align="flex-start" gap="md" wrap="wrap">
            <TextInput
              placeholder="Search by ID or entity name..."
              value={search}
              onChange={(e) => setSearch(e.currentTarget.value)}
              leftSection={<IconSearch size={16} />}
              style={{ flex: 2, minWidth: "200px" }}
              radius="md"
            />

            <Group gap="xs" style={{ flex: 1, justifyContent: 'flex-end' }}>
              <Button
                variant="light"
                radius="md"
                onClick={() => toggleFilters()}
                leftSection={<IconAdjustments size={16} />}
                style={{ minWidth: 'fit-content' }}
              >
                {showFilters ? "Hide Filters" : "Show Filters"}
              </Button>

              <SegmentedControl
                value={viewMode}
                onChange={(value) => setViewMode(value as 'table' | 'grid')}
                data={[
                  {
                    value: 'table',
                    label: (
                      <Center style={{ gap: 8 }}>
                        <IconCalendar size={16} />
                        {!isMobile && <Text>Table</Text>}
                      </Center>
                    ),
                  },
                  {
                    value: 'grid',
                    label: (
                      <Center style={{ gap: 8 }}>
                        <IconChartBar size={16} />
                        {!isMobile && <Text>Grid</Text>}
                      </Center>
                    ),
                  },
                ]}
              />
            </Group>
          </Flex>

          <FilterPanel
            filters={filters}
            setFilters={setFilters}
            onToggleFilters={toggleFilters}
            showFilters={showFilters}
          />

          <Card
            withBorder
            shadow="sm"
            radius="md"
            p="md"
            style={{ overflow: 'hidden' }}
          >
            <Flex justify="space-between" align="center" mb="md">
              <Group gap="xs">
                <Badge variant="light" radius="sm" size="lg">
                  {filteredTransactions.length} Transactions
                </Badge>

                {Object.keys(filters).length > 0 && (
                  <Badge
                    color="blue"
                    variant="dot"
                    size="lg"
                    rightSection={
                      <ActionIcon
                        size="xs"
                        radius="xl"
                        variant="transparent"
                        onClick={() => setFilters({})}
                      >
                        <IconX size={10} />
                      </ActionIcon>
                    }
                  >
                    Filters Applied
                  </Badge>
                )}
              </Group>

              <Menu shadow="md" width={200}>
                <Menu.Target>
                  <Button
                    variant="subtle"
                    color="gray"
                    size="xs"
                    leftSection={sortOrder === 'asc' ? (
                      <IconSortAscending size={16} />
                    ) : (
                      <IconSortDescending size={16} />
                    )}
                    rightSection={<IconChevronDown size={12} />}
                  >
                    Sort: {
                      sortBy === 'timestamp' ? 'Date' :
                        sortBy === 'risk_score' ? 'Risk' :
                          'Entities'
                    }
                  </Button>
                </Menu.Target>

                <Menu.Dropdown>
                  <Menu.Label>Sort by</Menu.Label>
                  <Menu.Item
                    leftSection={<IconSortDescending size={16} />}
                    onClick={() => { setSortBy('timestamp'); setSortOrder('desc'); }}
                  >
                    Newest first
                  </Menu.Item>
                  <Menu.Item
                    leftSection={<IconSortAscending size={16} />}
                    onClick={() => { setSortBy('timestamp'); setSortOrder('asc'); }}
                  >
                    Oldest first
                  </Menu.Item>
                  <Menu.Item
                    leftSection={<IconSortDescending size={16} />}
                    onClick={() => { setSortBy('risk_score'); setSortOrder('desc'); }}
                  >
                    Highest risk first
                  </Menu.Item>
                  <Menu.Item
                    leftSection={<IconSortAscending size={16} />}
                    onClick={() => { setSortBy('risk_score'); setSortOrder('asc'); }}
                  >
                    Lowest risk first
                  </Menu.Item>
                  <Menu.Item
                    leftSection={<IconSortDescending size={16} />}
                    onClick={() => { setSortBy('entities_count'); setSortOrder('desc'); }}
                  >
                    Most entities first
                  </Menu.Item>
                  <Menu.Item
                    leftSection={<IconSortAscending size={16} />}
                    onClick={() => { setSortBy('entities_count'); setSortOrder('asc'); }}
                  >
                    Fewest entities first
                  </Menu.Item>
                </Menu.Dropdown>
              </Menu>
            </Flex>

            {error ? (
              <Alert icon={<IconAlertCircle size={16} />} title="Error" color="red">
                {error}
                <Button
                  variant="light"
                  color="red"
                  onClick={handleRefresh}
                  leftSection={<IconRefresh size={16} />}
                  mt="md"
                >
                  Try Again
                </Button>
              </Alert>
            ) : (
              <>
                {displayTransactions.length > 0 ? (
                  <>
                    {viewMode === 'table' ? (
                      <ScrollArea>
                        <Table highlightOnHover withTableBorder withColumnBorders>
                          <Table.Thead>
                            <Table.Tr>
                            <Table.Th style={{ width: "50px" }}></Table.Th>
                              <Table.Th>Transaction ID</Table.Th>
                              <Table.Th>Date</Table.Th>
                              <Table.Th>Status</Table.Th>
                              <Table.Th>Risk Score</Table.Th>
                              <Table.Th>Entities</Table.Th>
                            </Table.Tr>
                          </Table.Thead>
                          <Table.Tbody>
                            {displayTransactions.map((transaction) => (
                              <Table.Tr key={transaction.transaction_id} className="table-row-hover">
                                <Table.Td>
                                  <Group gap={4} justify="center">
                                    <Tooltip label="View Details" withArrow position="top">
                                      <ActionIcon
                                        variant="light"
                                        color="blue"
                                        onClick={() => handleViewTransaction(transaction.transaction_id)}
                                      >
                                        <IconEye size={16} />
                                      </ActionIcon>
                                    </Tooltip>
                                  </Group>
                                </Table.Td>
                                <Table.Td>
                                  <Flex align="center" gap="xs">
                                    <ThemeIcon
                                      color={getRiskColor(transaction.risk_score)}
                                      variant="light"
                                      size="sm"
                                      radius="xl"
                                    >
                                      {transaction.risk_score >= 0.7 ? (
                                        <IconAlertTriangle size={12} />
                                      ) : transaction.risk_score >= 0.4 ? (
                                        <IconShield size={12} />
                                      ) : (
                                        <IconShieldCheck size={12} />
                                      )}
                                    </ThemeIcon>
                                    <Text fw={500} size="sm">{transaction.transaction_id}</Text>
                                  </Flex>
                                </Table.Td>
                                <Table.Td>
                                  <Flex align="center" gap="xs">
                                    <IconCalendar size={14} color={theme.colors.gray[6]} />
                                    <Text size="sm">{formatDate(transaction.timestamp)}</Text>
                                  </Flex>
                                </Table.Td>
                                <Table.Td>
                                  <Badge
                                    color={statusColors[transaction.status] || 'gray'}
                                    variant="filled"
                                    size="sm"
                                    radius="sm"
                                  >
                                    {transaction.status}
                                  </Badge>
                                </Table.Td>
                                <Table.Td>
                                  <Group gap={6}>
                                    <RingProgress
                                      size={30}
                                      thickness={3}
                                      roundCaps
                                      sections={[
                                        { value: transaction.risk_score * 100, color: getRiskColor(transaction.risk_score) }
                                      ]}
                                    />
                                    <Badge
                                      color={getRiskColor(transaction.risk_score)}
                                      variant="filled"
                                      size="sm"
                                    >
                                      {Math.round(transaction.risk_score * 100)}%
                                    </Badge>
                                  </Group>
                                </Table.Td>
                                <Table.Td>
                                  <Flex align="center" gap="xs">
                                    <ThemeIcon size="xs" radius="xl" color="blue" variant="light">
                                      <IconBuildingSkyscraper size={10} />
                                    </ThemeIcon>
                                    <Text size="sm">{transaction.entities_count}</Text>
                                  </Flex>
                                </Table.Td>
                                
                              </Table.Tr>
                            ))}
                          </Table.Tbody>
                        </Table>
                      </ScrollArea>
                    ) : (
                      <Grid gutter="md">
                        {displayTransactions.map((transaction) => (
                          <Grid.Col key={transaction.transaction_id} span={6}>
                            <TransactionCard
                              transaction={transaction}
                              onView={() => handleViewTransaction(transaction.transaction_id)}
                            />
                          </Grid.Col>
                        ))}
                      </Grid>
                    )}
                  </>
                ) : (
                  <EmptyState onSubmitNew={() => navigate('/submit')} />
                )}
              </>
            )}
          </Card>

          <Flex justify="space-between" align="center">
            <Pagination
              value={page}
              onChange={setPage}
              total={totalPages}
              siblings={1}
              size="xs"
            />

            <Text size="xs" color="dimmed">
              Page {page} of {totalPages}
            </Text>
          </Flex>
        </Flex>
      </Card>
    </Box>
  );
}
export default TransactionHistory;