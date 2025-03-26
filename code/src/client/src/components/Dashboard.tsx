import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Text, Title, Button, Group,
  SimpleGrid, Paper, Flex, Badge, Skeleton,
  Divider, ThemeIcon, Center, Box,
  Progress, useMantineTheme
} from '@mantine/core';
import {
  IconArrowUpRight, IconArrowDownRight, IconFileUpload,
  IconAlertTriangle, IconShieldCheck, IconReportMoney,
  IconCircleDashed, IconActivity, IconBusinessplan,
  IconUpload
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { fetchDashboardStats } from '../api/transactionApi';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, PieChart, Pie, Sector } from 'recharts';

interface StatsData {
  totalTransactions: number;
  highRiskTransactions: number;
  mediumRiskTransactions: number;
  lowRiskTransactions: number;
  recentTransactions: {
    id: string;
    timestamp: string;
    risk: number;
    status: string;
  }[];
}


// Enhanced transaction card component
interface Transaction {
  id: string;
  timestamp: string;
  risk: number;
  status: string;
}

interface TransactionCardProps {
  transaction: Transaction;
  loading?: boolean;
}

const TransactionCard: React.FC<TransactionCardProps> = ({ transaction, loading = false }) => {
  const theme = useMantineTheme();

  const getRiskColor = (risk: number) => {
    if (risk >= 0.7) return 'red';
    if (risk >= 0.4) return 'orange';
    return 'green';
  };

  const formatDate = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return timestamp;
    }
  };

  if (loading) {
    return (
      <Paper withBorder p="lg" radius="md" shadow="sm">
        <Flex align="center" gap="md">
          <Skeleton height={40} circle />
          <Box style={{ flex: 1 }}>
            <Skeleton height={18} width="70%" mb={8} />
            <Skeleton height={14} width="40%" />
          </Box>
          <Skeleton height={24} width={60} radius="md" />
        </Flex>
      </Paper>
    );
  }

  return (
    <Paper
      withBorder
      p="lg"
      radius="md"
      shadow="sm"
      style={{
        transition: 'transform 0.2s, box-shadow 0.2s',
        ':hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 5px 15px rgba(0,0,0,0.08)'
        }
      }}
    >
      <Flex align="center" justify="space-between">
        <Flex align="center" gap="md">
          <ThemeIcon
            size={40}
            radius="xl"
            color={getRiskColor(transaction.risk)}
            variant="light"
            style={{
              boxShadow: `0 0 20px ${theme.colors[getRiskColor(transaction.risk)][3]}`
            }}
          >
            {transaction.risk >= 0.7 ? (
              <IconAlertTriangle size={20} />
            ) : transaction.risk >= 0.4 ? (
              <IconCircleDashed size={20} />
            ) : (
              <IconShieldCheck size={20} />
            )}
          </ThemeIcon>

          <Box>
            <Text fw={500} component={Link} to={`/results/${transaction.id}`} style={{ textDecoration: 'none' }}>
              {transaction.id}
            </Text>
            <Text size="xs" c="dimmed">{formatDate(transaction.timestamp)}</Text>
          </Box>
        </Flex>

        <Badge
          color={getRiskColor(transaction.risk)}
          variant="filled"
          size="lg"
          radius="md"
          p="sm"
          style={{
            boxShadow: `0 2px 10px ${theme.colors[getRiskColor(transaction.risk)][2]}50`
          }}
        >
          {Math.round(transaction.risk * 100)}% Risk
        </Badge>
      </Flex>
    </Paper>
  );
};

// Active shape for pie chart (for hover effects)
interface ActiveShapeProps {
  cx: number;
  cy: number;
  innerRadius: number;
  outerRadius: number;
  startAngle: number;
  endAngle: number;
  fill: string;
  payload: {
    name: string;
  };
  percent: number;
  value: number;
}

const ActiveShape: React.FC<ActiveShapeProps> = (props) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent, value } = props;

  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 6}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 6}
        outerRadius={outerRadius + 10}
        fill={fill}
      />
      <text x={cx} y={cy} dy={-20} textAnchor="middle" fill="#888" fontSize={14}>
        {payload.name}
      </text>
      <text x={cx} y={cy} dy={8} textAnchor="middle" fill="#333" fontSize={16} fontWeight={600}>
        {value}
      </text>
      <text x={cx} y={cy} dy={25} textAnchor="middle" fill="#888" fontSize={12}>
        {`(${(percent * 100).toFixed(0)}%)`}
      </text>
    </g>
  );
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const theme = useMantineTheme();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<StatsData>({
    totalTransactions: 0,
    highRiskTransactions: 0,
    mediumRiskTransactions: 0,
    lowRiskTransactions: 0,
    recentTransactions: []
  });
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        const response = await fetchDashboardStats();
        setStats(response);
      } catch (error) {
        console.error("Failed to load dashboard stats:", error);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  // Prepare data for the charts
  const pieData = [
    { name: 'High Risk', value: stats.highRiskTransactions, color: theme.colors.red[6] },
    { name: 'Medium Risk', value: stats.mediumRiskTransactions, color: theme.colors.orange[6] },
    { name: 'Low Risk', value: stats.lowRiskTransactions, color: theme.colors.green[6] },
  ];

  const barData = [
    { name: 'High', value: stats.highRiskTransactions, color: theme.colors.red[6] },
    { name: 'Medium', value: stats.mediumRiskTransactions, color: theme.colors.orange[6] },
    { name: 'Low', value: stats.lowRiskTransactions, color: theme.colors.green[6] },
  ];

  interface PieEnterEvent {
    index: number;
  }

  const onPieEnter = (_: PieEnterEvent, index: number) => {
    setActiveIndex(index);
  };

  // Calculate risk trends (mock data - in real app would come from API)
  interface Trend {
    value: number;
    percentage: number;
    isPositive: boolean;
  }

  const calculateTrend = (current: number, previous: number): Trend => {
    const diff = current - previous;
    return {
      value: diff,
      percentage: previous === 0 ? 0 : (diff / previous) * 100,
      isPositive: diff >= 0
    };
  };

  const riskTrends = {
    high: calculateTrend(stats.highRiskTransactions, stats.highRiskTransactions * 0.8),
    medium: calculateTrend(stats.mediumRiskTransactions, stats.mediumRiskTransactions * 1.2),
    low: calculateTrend(stats.lowRiskTransactions, stats.lowRiskTransactions * 0.9)
  };

  return (
    <div>
      <Flex justify="space-between" align="center" mb="xl">
        <Box>
          <Title order={2} mb={4}>Risk Intelligence Dashboard</Title>
          <Text c="dimmed" size="sm">Overview of risk assessments and compliance metrics</Text>
        </Box>
        <Group>
          <Button
            leftSection={<IconUpload size={18} />}
            onClick={() => navigate('/bulk-upload')}
            variant="light"
            radius="md"
            size="md"
          >
            Bulk Upload
          </Button>
          <Button
            leftSection={<IconFileUpload size={18} />}
            onClick={() => navigate('/submit')}
            variant="gradient"
            gradient={{ from: theme.primaryColor, to: 'cyan', deg: 45 }}
            radius="md"
            size="md"
          >
            Submit New Transaction
          </Button>
        </Group>
      </Flex>

      {/* Stats Cards */}
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md" mb="xl">
        {/* Total Transactions Card */}
        <Paper withBorder p="lg" radius="md" shadow="sm">
          <Group justify="space-between">
            <Box>
              <Text tt="uppercase" fw={500} size="xs" c="dimmed">
                Total Transactions
              </Text>
              <Skeleton height={36} width={90} visible={loading}>
                <Title order={2}>{stats.totalTransactions}</Title>
              </Skeleton>
            </Box>
            <ThemeIcon
              size={48}
              radius="md"
              variant="gradient"
              gradient={{ from: 'blue', to: 'cyan' }}
            >
              <IconBusinessplan size={24} />
            </ThemeIcon>
          </Group>
          <Divider my="sm" />
          <Group mt="xs">
            <Flex align="center" gap={4}>
              <ThemeIcon
                color="gray"
                variant="light"
                size="sm"
                radius="xl"
              >
                <IconActivity size={12} />
              </ThemeIcon>
              <Text size="xs" c="dimmed">Last 30 days</Text>
            </Flex>
          </Group>
        </Paper>

        {/* High Risk Card */}
        <Paper withBorder p="lg" radius="md" shadow="sm">
          <Group justify="space-between">
            <Box>
              <Text tt="uppercase" fw={500} size="xs" c="dimmed">
                High Risk
              </Text>
              <Group align="flex-end" gap={8}>
                <Skeleton height={36} width={50} visible={loading}>
                  <Title order={2}>{stats.highRiskTransactions}</Title>
                </Skeleton>
                <Badge color="red" size="lg" variant="filled">
                  {Math.round(stats.highRiskTransactions / (stats.totalTransactions || 1) * 100)}%
                </Badge>
              </Group>
            </Box>
            <ThemeIcon
              size={48}
              radius="md"
              variant="gradient"
              gradient={{ from: 'red', to: 'pink' }}
            >
              <IconAlertTriangle size={24} />
            </ThemeIcon>
          </Group>
          <Divider my="sm" />
          <Group mt="xs">
            <Flex align="center" gap={4}>
              {riskTrends.high.isPositive ? (
                <IconArrowUpRight size={14} color={theme.colors.red[6]} />
              ) : (
                <IconArrowDownRight size={14} color={theme.colors.green[6]} />
              )}
              <Text
                size="xs"
                fw={500}
                c={riskTrends.high.isPositive ? 'red' : 'green'}
              >
                {Math.abs(riskTrends.high.percentage).toFixed(1)}%
              </Text>
              <Text size="xs" c="dimmed">from previous period</Text>
            </Flex>
          </Group>
        </Paper>

        {/* Medium Risk Card */}
        <Paper withBorder p="lg" radius="md" shadow="sm">
          <Group justify="space-between">
            <Box>
              <Text tt="uppercase" fw={500} size="xs" c="dimmed">
                Medium Risk
              </Text>
              <Group align="flex-end" gap={8}>
                <Skeleton height={36} width={50} visible={loading}>
                  <Title order={2}>{stats.mediumRiskTransactions}</Title>
                </Skeleton>
                <Badge color="orange" size="lg" variant="filled">
                  {Math.round(stats.mediumRiskTransactions / (stats.totalTransactions || 1) * 100)}%
                </Badge>
              </Group>
            </Box>
            <ThemeIcon
              size={48}
              radius="md"
              variant="gradient"
              gradient={{ from: 'orange', to: 'yellow' }}
            >
              <IconCircleDashed size={24} />
            </ThemeIcon>
          </Group>
          <Divider my="sm" />
          <Group mt="xs">
            <Flex align="center" gap={4}>
              {riskTrends.medium.isPositive ? (
                <IconArrowUpRight size={14} color={theme.colors.red[6]} />
              ) : (
                <IconArrowDownRight size={14} color={theme.colors.green[6]} />
              )}
              <Text
                size="xs"
                fw={500}
                c={riskTrends.medium.isPositive ? 'red' : 'green'}
              >
                {Math.abs(riskTrends.medium.percentage).toFixed(1)}%
              </Text>
              <Text size="xs" c="dimmed">from previous period</Text>
            </Flex>
          </Group>
        </Paper>

        {/* Low Risk Card */}
        <Paper withBorder p="lg" radius="md" shadow="sm">
          <Group justify="space-between">
            <Box>
              <Text tt="uppercase" fw={500} size="xs" c="dimmed">
                Low Risk
              </Text>
              <Group align="flex-end" gap={8}>
                <Skeleton height={36} width={50} visible={loading}>
                  <Title order={2}>{stats.lowRiskTransactions}</Title>
                </Skeleton>
                <Badge color="green" size="lg" variant="filled">
                  {Math.round(stats.lowRiskTransactions / (stats.totalTransactions || 1) * 100)}%
                </Badge>
              </Group>
            </Box>
            <ThemeIcon
              size={48}
              radius="md"
              variant="gradient"
              gradient={{ from: 'green', to: 'teal' }}
            >
              <IconShieldCheck size={24} />
            </ThemeIcon>
          </Group>
          <Divider my="sm" />
          <Group mt="xs">
            <Flex align="center" gap={4}>
              {riskTrends.low.isPositive ? (
                <IconArrowUpRight size={14} color={theme.colors.green[6]} />
              ) : (
                <IconArrowDownRight size={14} color={theme.colors.red[6]} />
              )}
              <Text
                size="xs"
                fw={500}
                c={riskTrends.low.isPositive ? 'green' : 'red'}
              >
                {Math.abs(riskTrends.low.percentage).toFixed(1)}%
              </Text>
              <Text size="xs" c="dimmed">from previous period</Text>
            </Flex>
          </Group>
        </Paper>
      </SimpleGrid>

      <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="md" mb="xl">
        {/* Recent Transactions Card */}
        <Paper withBorder radius="md" shadow="sm" p="lg">
          <Flex justify="space-between" align="center" mb="lg">
            <Title order={4}>Recent Transactions</Title>
            <Badge variant="outline">Last 7 days</Badge>
          </Flex>

          <Flex direction="column" gap="md">
            {loading ? (
              Array(3).fill(0).map((_, i) => (
                <TransactionCard key={i} transaction={{ id: '', timestamp: '', risk: 0, status: '' }} loading={true} />
              ))
            ) : stats.recentTransactions.length > 0 ? (
              stats.recentTransactions.map((transaction) => (
                <TransactionCard
                  key={transaction.id}
                  transaction={transaction}
                />
              ))
            ) : (
              <Center py="xl">
                <Flex direction="column" align="center" gap="md">
                  <ThemeIcon size={48} radius="xl" color="gray" variant="light">
                    <IconReportMoney size={24} />
                  </ThemeIcon>
                  <Text c="dimmed">No recent transactions found</Text>
                  <Button
                    variant="light"
                    component={Link}
                    to="/submit"
                    leftSection={<IconFileUpload size={16} />}
                  >
                    Submit Your First Transaction
                  </Button>
                </Flex>
              </Center>
            )}

            {stats.recentTransactions.length > 0 && (
              <Button
                variant="subtle"
                fullWidth
                mt="md"
                component={Link}
                to="/history"
                rightSection={<IconArrowUpRight size={16} />}
              >
                View All Transactions
              </Button>
            )}
          </Flex>
        </Paper>

        {/* Risk Distribution Card */}
        <Paper withBorder radius="md" shadow="sm" p="lg">
          <Title order={4} mb="lg">Risk Distribution Analytics</Title>

          {loading ? (
            <Center h={300}>
              <Skeleton height={250} radius="md" width="100%" />
            </Center>
          ) : (
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
              {/* Pie Chart */}
              <Box>
                <Center>
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        activeIndex={activeIndex}
                        activeShape={ActiveShape}
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        fill="#8884d8"
                        paddingAngle={5}
                        dataKey="value"
                        onMouseEnter={onPieEnter}
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </Center>

                <Flex justify="center" gap="lg" mt="md">
                  {pieData.map((item, index) => (
                    <Flex key={index} align="center" gap="xs">
                      <Box style={{ width: 12, height: 12, backgroundColor: item.color, borderRadius: '50%' }} />
                      <Text size="sm">{item.name}</Text>
                    </Flex>
                  ))}
                </Flex>
              </Box>

              {/* Bar Chart */}
              <Box>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={barData} layout="vertical" margin={{ left: 0, right: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} />
                    <RechartsTooltip
                      formatter={(value) => [`${value} Transactions`, 'Count']}
                      contentStyle={{ borderRadius: '4px' }}
                    />
                    <Bar dataKey="value" key="name" radius={[0, 4, 4, 0]}>
                      {barData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>

                <Box mt="md">
                  {barData.map((item, index) => (
                    <Box key={index} mb="xs">
                      <Flex justify="space-between" align="center" mb={4}>
                        <Text size="xs" fw={500}>{item.name} Risk</Text>
                        <Text size="xs" fw={600}>{item.value}</Text>
                      </Flex>
                      <Progress
                        value={(item.value / stats.totalTransactions) * 100}
                        color={item.color}
                        size="sm"
                        radius="xl"
                      />
                    </Box>
                  ))}
                </Box>
              </Box>
            </SimpleGrid>
          )}
        </Paper>
      </SimpleGrid>

    </div>
  );
};


export default Dashboard;