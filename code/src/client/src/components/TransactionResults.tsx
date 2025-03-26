// components/TransactionResults.tsx
import React, { useState, useEffect, JSX } from 'react';
import { useParams, Link } from 'react-router-dom';
import TransactionFiles from './TransactionFiles';
import {
  Title, Text, Card, Badge, Grid, Progress,
  Group, Button, Tabs, Box,
  Paper, Flex, Divider, Loader, Alert, ScrollArea, Code, Collapse,
  ThemeIcon, RingProgress, Center, useMantineTheme,
  Container, ActionIcon, Space,
  Avatar, Tooltip, List,
  Modal,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconSearch,
  IconBuilding, IconUser, IconShield,
  IconArrowsExchange,
  IconArrowBack, IconRefresh, IconAlertTriangle, IconInfoCircle,
  IconBuildingBank, IconReportMoney, IconUsersGroup, IconShieldLock,
  IconX, IconFileUpload, IconEye,
  IconCheck, IconExclamationMark,
  IconNetworkOff, IconChartBar, IconFolder, IconNetwork,
  IconHistory
} from '@tabler/icons-react';
import EntityNetworkViz from './EntityNetworkViz';
import EntityHistory from './EntityHistory';


import { getTransactionStatus, getTaskResults } from '../api/transactionApi';

interface TaskResult {
  task_id: string;
  status: 'success' | 'failed' | 'running' | 'pending';
  start_time: string;
  end_time?: string;
  result?: any;
}

interface TransactionResult {
  transaction_id: string;
  status: 'completed' | 'processing' | 'failed';
  extracted_entities: string[];
  entity_types: string[];
  risk_score: number;
  supporting_evidence: string[];
  confidence_score: number;
  reason: string;
  tasks?: TaskResult[];
  raw_data?: {
    transaction_text?: string;
  };
  timestamp?: string;
}

const getRiskColor = (score: number) => {
  if (score >= 0.7) return 'red';
  if (score >= 0.4) return 'yellow';
  return 'green';
};

const getRiskLabel = (score: number) => {
  if (score >= 0.7) return 'High Risk';
  if (score >= 0.4) return 'Medium Risk';
  return 'Low Risk';
};

const EntityCard: React.FC<{ entity: string, type: string, transactionId: string }> = ({ entity, type, transactionId }) => {
  const theme = useMantineTheme();
  const [hovered, setHovered] = useState(false);

  const entityTypeIcons: Record<string, JSX.Element> = {
    'Corporation': <IconBuilding size={20} stroke={1.5} />,
    'Shell Company': <IconShieldLock size={20} stroke={1.5} />,
    'Non Profit': <IconBuildingBank size={20} stroke={1.5} />,
    'Financial Institution': <IconReportMoney size={20} stroke={1.5} />,
    'Government Agency': <IconBuildingBank size={20} stroke={1.5} />,
    'Person': <IconUser size={20} stroke={1.5} />,
    'PEP': <IconUsersGroup size={20} stroke={1.5} />
  };

  const getEntityColor = (type: string) => {
    switch (type) {
      case 'Corporation': return 'blue';
      case 'Shell Company': return 'red';
      case 'Non Profit': return 'green';
      case 'Financial Institution': return 'indigo';
      case 'Government Agency': return 'orange';
      case 'Person': return 'violet';
      case 'PEP': return 'pink';
      default: return 'gray';
    }
  };

  const defaultIcon = <IconInfoCircle size={20} stroke={1.5} />;
  const iconForType = entityTypeIcons[type] || defaultIcon;
  const [showHistory, { open, close }] = useDisclosure(false);


  return (
    <>
      <Paper
        withBorder
        p="md"
        radius="md"
        shadow={hovered ? "md" : "sm"}
        style={{
          transition: 'all 0.2s ease',
          transform: hovered ? 'translateY(-5px)' : 'none',
          cursor: 'pointer',
          position: 'relative',
          overflow: 'hidden'
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {/* Decorative corner stripe */}
        <Box
          style={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: '30px',
            height: '30px',
            background: theme.colors[getEntityColor(type)][4],
            clipPath: 'polygon(0 0, 100% 0, 100% 100%)',
            transition: 'all 0.2s ease',
            opacity: hovered ? 0.9 : 0.6
          }}
        />

        <Flex gap="sm">
          <Avatar
            size="md"
            radius="md"
            color={getEntityColor(type)}
            variant="filled"
          >
            {iconForType}
          </Avatar>
          <Box>
            <Tooltip label={`View details for ${entity}`} position="top" withArrow>
              <Text fw={600} lineClamp={1}>{entity}</Text>
            </Tooltip>
            <Badge
              variant="dot"
              color={getEntityColor(type)}
              size="sm"
            >
              {type}
            </Badge>
          </Box>
        </Flex>

        {hovered && (
          <Group justify="right" style={{ position: 'absolute', bottom: '8px', right: '8px' }}>
            <Tooltip label={showHistory ? "Hide history" : "View history"}>
              <ActionIcon
                variant="subtle"
                color="blue"
                onClick={(e) => {
                  e.stopPropagation();
                  open();
                }}
              >
                <IconHistory size={16} />
              </ActionIcon>
            </Tooltip>
          </Group>
        )}

      </Paper>

      <Modal opened={showHistory} onClose={close} title="History" centered size={"xl"}>
        <EntityHistory
          entityName={entity}
          entityType={type}
          transactionId={transactionId || ''}
        />
      </Modal>
    </>
  );
};

const EvidenceCard: React.FC<{ evidence: string, index: number }> = ({ evidence, index }) => {
  const theme = useMantineTheme();

  return (
    <Paper withBorder p="md" radius="md" mb="md">
      <Group justify="apart" mb="xs">
        <Flex gap="sm">
          <ThemeIcon
            size="md"
            radius="xl"
            variant="light"
            color={index % 2 === 0 ? theme.primaryColor : 'teal'}
          >
            {index % 2 === 0 ?
              <IconInfoCircle size={16} /> :
              <IconExclamationMark size={16} />
            }
          </ThemeIcon>
          <Text size="sm" fw={500}>Evidence #{index + 1}</Text>
        </Flex>
        <Badge
          variant="outline"
          color={index % 2 === 0 ? theme.primaryColor : 'teal'}
          size="sm"
        >
          {index % 2 === 0 ? 'Insight' : 'Warning'}
        </Badge>
      </Group>
      <Text size="sm">{evidence}</Text>
    </Paper>
  );
};

const TransactionResults: React.FC = () => {
  const { transactionId = '' } = useParams<{ transactionId: string }>() || { transactionId: '' };
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<TransactionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string | null>('overview');
  const [refreshInterval, setRefreshInterval] = useState<ReturnType<typeof setInterval> | null>(null);
  const [showReason, { toggle: toggleReason }] = useDisclosure(false);
  const [showRawText, { toggle: toggleRawText }] = useDisclosure(false);
  const theme = useMantineTheme();

  const fetchResults = async () => {
    if (!transactionId) return;

    try {
      setLoading(true);
      const data = await getTransactionStatus(transactionId);

      if (data.status === 'processing' || data.status === 'airflow_processing') {
        // If still processing, get task details
        try {
          const taskResults = await getTaskResults(transactionId);
          data.tasks = taskResults;
        } catch (err) {
          console.warn("Could not fetch task details:", err);
        }
      }

      setResult(data);

      // Stop polling if processing is complete
      if (data.status === 'completed' || data.status === 'failed') {
        if (refreshInterval) {
          clearInterval(refreshInterval);
          setRefreshInterval(null);
        }
      }

      setError(null);
    } catch (err) {
      console.error("Error fetching transaction status:", err);
      setError("Failed to load transaction results. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();

    // Set up polling for updates if the transaction is still processing
    if (!refreshInterval) {
      const interval = setInterval(fetchResults, 60000);
      setRefreshInterval(interval);
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [transactionId]);

  const handleRefresh = () => {
    fetchResults();
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  if (loading && !result) {
    return (
      <Container p={0} style={{ position: 'relative' }}>
        <Paper
          radius="md"
          shadow="md"
          p="xl"
          style={{
            height: '60vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            background: `linear-gradient(to bottom right, rgba(173, 216, 230, 0.7), rgba(240, 248, 255, 0.3))`,
            backdropFilter: 'blur(10px)',
            border: `1px solid ${theme.colors.gray[2]}`
          }}
        >
          <Loader size="xl" variant="dots" color={theme.primaryColor} />
          <Space h="md" />
          <Title order={3}>Loading Transaction Assessment</Title>
          <Text c="dimmed" size="sm" mt="xs" maw={400}>
            Please wait while we retrieve the risk assessment data for transaction {transactionId}...
          </Text>
        </Paper>
      </Container>
    );
  }

  if (error) {
    return (
      <Alert
        icon={<IconNetworkOff size={28} />}
        title="Error Loading Results"
        color="red"
        variant="filled"
        radius="md"
      >
        <Text mb="md">{error}</Text>
        <Group>
          <Button
            variant="white"
            color="red"
            onClick={handleRefresh}
            leftSection={<IconRefresh size={16} />}
          >
            Try Again
          </Button>
          <Button
            variant="subtle"
            color="white"
            component={Link}
            to="/"
            leftSection={<IconArrowBack size={16} />}
          >
            Back to Dashboard
          </Button>
        </Group>
      </Alert>
    );
  }

  if (!result) {
    return (
      <Paper withBorder p="xl" radius="md" shadow="md">
        <Flex direction="column" gap="md">
          <ThemeIcon size={60} radius="xl" color="blue" variant="light">
            <IconInfoCircle size={30} />
          </ThemeIcon>
          <Title order={2}>No Results Found</Title>
          <Text maw={500} size="lg" c="dimmed">
            No results found for transaction ID: <b>{transactionId}</b>
          </Text>
          <Group mt="md">
            <Button
              component={Link}
              to="/submit"
              size="md"
              variant="light"
              leftSection={<IconFileUpload size={20} />}
            >
              Submit a New Transaction
            </Button>
            <Button
              variant="filled"
              size="md"
              onClick={handleRefresh}
              leftSection={<IconRefresh size={20} />}
            >
              Refresh
            </Button>
          </Group>
        </Flex>
      </Paper>
    );
  }

  const isProcessing = result.status === 'processing';
  const completedTasks = result.tasks?.filter(t => t.status === 'success').length || 0;
  const totalTasks = result.tasks?.length || 1;
  const progressPercentage = (completedTasks / totalTasks) * 100;
  // const [filesLoaded, setFilesLoaded] = useState(false);

  return (
    <div className="fade-in">
      {/* Header Section */}
      <Box mb="lg" style={{ position: 'relative' }}>
        <Paper
          radius="lg"
          p="md"
          style={{
            background: `linear-gradient(45deg, rgba(66, 153, 225, 0.8), rgba(75, 85, 205, 0.9))`,
            color: '#fff',
            overflow: 'hidden',
            position: 'relative'
          }}
        >
          <Flex justify="space-between" wrap="wrap">
            <Flex gap="md">
              <Box>
                <Title order={2} c="white">Transaction Assessment</Title>
                <Text color="white" opacity={0.9}>ID: {result.transaction_id || transactionId}</Text>
              </Box>
            </Flex>
            <Group>
              <Button
                onClick={handleRefresh}
                variant="white"
                leftSection={<IconRefresh size={16} />}
                loading={isProcessing}
                radius="xl"
                color="dark"
              >
                {isProcessing ? 'Refreshing...' : 'Refresh'}
              </Button>
              <Button
                component={Link}
                to="/submit"
                variant="white"
                leftSection={<IconArrowBack size={16} />}
                size="sm"
                radius="xl"
                color="dark"
              >
                New Transaction
              </Button>

            </Group>
          </Flex>

          {/* Decorative elements */}
          <Box style={{
            position: 'absolute',
            top: -100,
            right: -100,
            width: 300,
            height: 300,
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.1)',
            zIndex: 0
          }} />

          <Box style={{
            position: 'absolute',
            bottom: -80,
            left: -80,
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'rgba(255, 255, 255, 0.07)',
            zIndex: 0
          }} />
        </Paper>
      </Box>

      {/* Raw transaction text modal */}
      {showRawText && result.raw_data?.transaction_text && (
        <Paper withBorder mb="lg" p="md" radius="md" shadow="sm">
          <Group justify="apart" mb="md">
            <Title order={4}>Raw Transaction Data</Title>
            <ActionIcon onClick={toggleRawText} variant="subtle">
              <IconX size={18} />
            </ActionIcon>
          </Group>
          <ScrollArea h={200} type="auto">
            <Code block>{result.raw_data.transaction_text}</Code>
          </ScrollArea>
        </Paper>
      )}

      {/* Processing status card */}
      {isProcessing && (
        <Card withBorder shadow="md" radius="md" mb="xl" p="lg" className="glass-card">
          <Flex direction="column" gap="md">
            <Group justify="apart">
              <Box>
                <Title order={3} mb={4}>Processing Transaction</Title>
                <Text c="dimmed">Your transaction is being analyzed by our AI system</Text>
              </Box>
              <Badge
                color="blue"
                size="xl"
                radius="md"
                variant="filled"
                p="md"
                style={{ fontSize: '1rem' }}
                className="pulse"
              >
                PROCESSING
              </Badge>
            </Group>

            <Paper withBorder p="lg" radius="md" bg={`rgba(${theme.colors.blue[0]}, 0.5)`}>
              <Text fw={500} mb="sm">Analysis Progress</Text>
              <Progress
                value={progressPercentage}
                size="xl"
                radius="xl"
                striped
                animated={isProcessing}
                color={theme.primaryColor}
                mb="md"
              />

              <Flex gap="md" justify="center">
                <Loader size="sm" color={theme.primaryColor} />
                <Text fw={500} c={theme.primaryColor}>
                  {completedTasks} of {totalTasks} tasks completed
                </Text>
              </Flex>

              <Text size="sm" c="dimmed" mt="md">
                Analysis typically takes 30-60 seconds. You'll be notified when it's complete.
              </Text>
            </Paper>
          </Flex>
        </Card>
      )}

      {/* Main content tabs */}
      <Tabs
        value={activeTab}
        onChange={setActiveTab}
        variant="pills"
        radius="md"
        color={result.status === 'completed' ? getRiskColor(result.risk_score) : 'blue'}
      >
        <Tabs.List grow mb="md">
          <Tabs.Tab
            value="overview"
            leftSection={<IconChartBar size={16} />}
            fw={500}
          >
            Risk Overview
          </Tabs.Tab>
          <Tabs.Tab
            value="entities"
            leftSection={<IconSearch size={16} />}
            fw={500}
          >
            Detected Entities
          </Tabs.Tab>
          <Tabs.Tab
            value="tasks"
            leftSection={<IconArrowsExchange size={16} />}
            fw={500}
          >
            Knowledge Base
          </Tabs.Tab>
          <Tabs.Tab
            value="network"
            leftSection={<IconNetwork size={16} />}
            fw={500}
          >
            Network Analysis
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="network" pt="md">
          <Paper withBorder radius="md" shadow="sm" p="xl">
            <Title order={4} mb="xl">Entity Network Analysis</Title>
            <Text mb="lg">
              This visualization shows the relationships between entities involved in this transaction and their connections to other entities based on historical data.
            </Text>

            <EntityNetworkViz transactionId={result.transaction_id || transactionId || ''} />
          </Paper>
        </Tabs.Panel>

        {/* Overview Tab */}
        <Tabs.Panel value="overview" pt="md">
          {result.status === 'completed' ? (
            <Grid>
              <Grid.Col span={{ base: 12, md: 8 }}>
                <Card withBorder radius="md" shadow="sm" p="lg" className="scale-in">
                  {/* Risk score header with gradient background */}
                  <Paper
                    p="lg"
                    radius="md"
                    mb="lg"
                    style={{
                      background: `linear-gradient(45deg, ${theme.colors[getRiskColor(result.risk_score)][7]}, ${theme.colors[getRiskColor(result.risk_score)][9]})`,
                      color: 'white',
                      position: 'relative',
                      overflow: 'hidden'
                    }}
                  >
                    <Flex justify="space-between" align="flex-start">
                      <Box>
                        <Title order={3} c="white" mb="xs">Risk Assessment</Title>
                        <Text color="white" opacity={0.9}>
                          {result.transaction_id}
                        </Text>
                        <Badge
                          mt="xs"
                          size="lg"
                          radius="md"
                          color="white"
                          variant="filled"
                          style={{
                            color: theme.colors[getRiskColor(result.risk_score)][9],
                            fontWeight: 700
                          }}
                        >
                          {getRiskLabel(result.risk_score)}
                        </Badge>
                      </Box>
                      <Box style={{ textAlign: 'center' }}>
                        <RingProgress
                          size={120}
                          roundCaps
                          thickness={12}
                          sections={[{
                            value: result.risk_score * 100,
                            color: "white",
                            tooltip: `${Math.round(result.risk_score * 100)}% Risk Score`
                          }]}
                          label={
                            <Center>
                              <Text fw={700} ta="center" size="xl" color="white">
                                {Math.round(result.risk_score * 100)}%
                              </Text>
                            </Center>
                          }
                        />
                      </Box>
                    </Flex>

                    {/* Decorative circles */}
                    <Box style={{
                      position: 'absolute',
                      bottom: -20,
                      right: -20,
                      width: 100,
                      height: 100,
                      borderRadius: '50%',
                      background: 'rgba(255, 255, 255, 0.1)',
                      zIndex: 0
                    }} />

                    <Box style={{
                      position: 'absolute',
                      top: -30,
                      left: -30,
                      width: 80,
                      height: 80,
                      borderRadius: '50%',
                      background: 'rgba(255, 255, 255, 0.1)',
                      zIndex: 0
                    }} />
                  </Paper>

                  <Button
                    onClick={toggleReason}
                    fullWidth
                    variant={showReason ? "filled" : "light"}
                    color={getRiskColor(result.risk_score)}
                    mb="md"
                    leftSection={showReason ? <IconX size={16} /> : <IconEye size={16} />}
                    radius="md"
                  >
                    {showReason ? 'Hide Detailed Analysis' : 'Show Detailed Risk Analysis'}
                  </Button>

                  <Collapse in={showReason}>
                    <Paper
                      withBorder
                      p="lg"
                      radius="md"
                      mb="lg"
                      bg={theme.colors.gray[0]}
                    >
                      <Text fw={600} mb="xs" size="lg">Compliance Officer's Analysis:</Text>
                      <Text>{result.reason}</Text>

                      <Grid mt="lg">
                        <Grid.Col span={6}>
                          <Card
                            withBorder
                            padding="sm"
                            shadow="sm"
                            bg={'white'}
                          >
                            <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Date</Text>
                            <Text fw={500}>{formatTimestamp(result.timestamp)}</Text>
                          </Card>
                        </Grid.Col>
                        <Grid.Col span={6}>
                          <Card
                            withBorder
                            padding="sm"
                            radius="md"
                            shadow="sm"
                            bg={'white'}
                          >
                            <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Confidence</Text>
                            <Group justify="apart">
                              <Text fw={500}>{Math.round(result.confidence_score * 100)}%</Text>
                              <Progress
                                value={result.confidence_score * 100}
                                color={theme.primaryColor}
                                size="sm"
                                radius="xl"
                                style={{ width: 60 }}
                              />
                            </Group>
                          </Card>
                        </Grid.Col>
                      </Grid>
                    </Paper>
                  </Collapse>

                  <Divider
                    my="md"
                    label={
                      <Group>
                        <IconShield size={16} />
                        <Text fw={500}>Supporting Evidence</Text>
                      </Group>
                    }
                    labelPosition="center"
                  />

                  <ScrollArea h={300} type="auto" offsetScrollbars>
                    {result.supporting_evidence.map((evidence, index) => (
                      <EvidenceCard key={index} evidence={evidence} index={index} />
                    ))}
                  </ScrollArea>
                </Card>
              </Grid.Col>

              <Grid.Col span={{ base: 12, md: 4 }}>
                <Card withBorder radius="md" shadow="sm" h="100%" p="lg" className="scale-in">
                  <Title order={4} mb="xl">Assessment Overview</Title>

                  <Flex direction="column" gap="lg">
                    <Card withBorder p="md" radius="md" bg={theme.colors.gray[0]}>
                      <Text size="xs" tt="uppercase" c="dimmed" fw={500} mb={4}>TRANSACTION ID</Text>
                      <Flex gap="sm">
                        <ThemeIcon size="md" radius="md" color="blue" variant="light">
                          <IconFolder size={16} />
                        </ThemeIcon>
                        <Text fw={600}>{result.transaction_id}</Text>
                      </Flex>
                    </Card>

                    <Card withBorder p="md" radius="md" bg={theme.colors.gray[0]}>
                      <Text size="xs" tt="uppercase" c="dimmed" fw={500} mb={4}>CONFIDENCE LEVEL</Text>
                      <Flex direction="column">
                        <Text fw={600} mb={8}>{(result.confidence_score * 100).toFixed(1)}%</Text>
                        <Progress
                          value={result.confidence_score * 100}
                          size="lg"
                          radius="xl"
                          color={theme.primaryColor}
                          striped
                        />
                      </Flex>
                    </Card>

                    <Card withBorder p="md" radius="md" bg={theme.colors.gray[0]}>
                      <Text size="xs" tt="uppercase" c="dimmed" fw={500} mb={4}>KEY FINDINGS</Text>
                      <List spacing="xs" size="sm" center icon={
                        <ThemeIcon color={theme.primaryColor} size={20} radius="xl">
                          <IconCheck size={12} />
                        </ThemeIcon>
                      }>
                        <List.Item>
                          <Text fw={500}>{result.extracted_entities.length} Entities Analyzed</Text>
                        </List.Item>
                        <List.Item>
                          <Text fw={500}>{result.entity_types.filter(t => t === 'Person' || t === 'PEP').length} People Identified</Text>
                        </List.Item>
                        <List.Item>
                          <Text fw={500}>{result.entity_types.filter(t => t === 'Corporation' || t === 'Shell Company' || t === 'Financial Institution').length} Organizations</Text>
                        </List.Item>
                        <List.Item>
                          <Text fw={500}>{result.supporting_evidence.length} Evidence Points</Text>
                        </List.Item>
                      </List>
                    </Card>
                  </Flex>
                </Card>
              </Grid.Col>
            </Grid>
          ) : (
            <Alert
              icon={<IconAlertTriangle size={24} />}
              color="yellow"
              title="Processing Incomplete"
              radius="md"
              p="lg"
            >
              <Text mb="md">
                The transaction is still being processed. Please check the Task Progress tab for detailed status information.
              </Text>
              <Button
                variant="light"
                color="yellow"
                leftSection={<IconRefresh size={16} />}
                onClick={handleRefresh}
              >
                Refresh Status
              </Button>
            </Alert>
          )}
        </Tabs.Panel>

        {/* Entities Tab */}
        <Tabs.Panel value="entities" pt="md">
          <Card withBorder radius="md" shadow="sm" mb="lg" p="lg" className="scale-in">
            <Flex justify="space-between" mb="lg">
              <Box>
                <Title order={4} mb={4}>Extracted Entities</Title>
                <Text size="sm" c="dimmed">Organizations, individuals, and other entities identified in the transaction</Text>
              </Box>

              <Badge
                size="lg"
                radius="md"
                variant="filled"
                color={theme.primaryColor}
              >
                {result.extracted_entities?.length || 0} Entities
              </Badge>
            </Flex>

            {result.extracted_entities && result.extracted_entities.length > 0 ? (
              <Grid>
                {result.extracted_entities.map((entity, index) => (
                  <Grid.Col key={index} span={{ base: 12, sm: 6, md: 4 }}>
                    <EntityCard
                      entity={entity}
                      type={result.entity_types && result.entity_types[index] ? result.entity_types[index] : 'Unknown'}
                      transactionId={transactionId}
                    />
                  </Grid.Col>
                ))}
              </Grid>
            ) : (
              <Center py="xl">
                <Flex direction="column" gap="md">
                  <ThemeIcon size={60} radius="xl" color="gray" variant="light">
                    <IconSearch size={30} />
                  </ThemeIcon>
                  <Text c="dimmed" size="lg">No entities extracted yet</Text>
                  {isProcessing && (
                    <Button
                      variant="light"
                      leftSection={<IconRefresh size={16} />}
                      onClick={handleRefresh}
                    >
                      Refresh
                    </Button>
                  )}
                </Flex>
              </Center>
            )}
          </Card>
        </Tabs.Panel>

        {/* Tasks Tab */}
        <Tabs.Panel value="tasks" pt="md">
          {/* Existing task timeline content */}

          {/* Add a space between sections */}
          <Space h="xl" />

          {/* Add the TransactionFiles component */}
          <TransactionFiles
            transactionId={result.transaction_id || transactionId || ''}
            isProcessing={isProcessing}
          />
        </Tabs.Panel>
      </Tabs>
    </div>
  );
}

export default TransactionResults;