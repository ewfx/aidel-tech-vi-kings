// client/src/components/EntityHistory.tsx
import React, { useState, useEffect } from 'react';
import {
  Text, Paper, Group, Flex, ThemeIcon,
  Badge, Loader, Alert, Divider, ScrollArea, Card, Tooltip, Grid, RingProgress,
  Center, useMantineTheme, ActionIcon, Collapse, Timeline, Table, Accordion
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconHistory, IconAlertCircle, IconInfoCircle,
  IconChartBar, IconCalendarStats, IconNetwork, 
  IconShield, IconBuildingBank, IconUsers, 
  IconChevronRight
} from '@tabler/icons-react';
import { API_URL } from '../api/constants';

interface EntityHistoryProps {
  entityName: string;
  entityType?: string;
  transactionId?: string;
}

interface HistoryData {
  status: string;
  message?: string;
  data?: {
    organization?: {
      properties: Record<string, any>;
      transactions: string[];
      transaction_count: number;
      avg_risk_score: number;
      max_risk_score: number;
      min_risk_score: number;
      first_seen: string;
      last_seen: string;
      related_people: {
        name: string;
        role: string;
        since: string;
      }[];
    };
    person?: {
      properties: Record<string, any>;
      transactions: string[];
      transaction_count: number;
      avg_risk_score: number;
      max_risk_score: number;
      min_risk_score: number;
      first_seen: string;
      last_seen: string;
      related_organizations: {
        name: string;
        role: string;
        since: string;
      }[];
    };
  };
}

const EntityHistory: React.FC<EntityHistoryProps> = ({ entityName, entityType, transactionId }) => {
  const [loading, setLoading] = useState(true);
  const [historyData, setHistoryData] = useState<HistoryData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, { toggle }] = useDisclosure(false);
  const theme = useMantineTheme();

  useEffect(() => {
    fetchHistory();
  }, [entityName, entityType, transactionId]);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      let url;
      if (transactionId) {
        // If transaction ID is provided, use the transaction history endpoint
        url = `${API_URL}/transaction/${transactionId}/history`;
      } else {
        // Otherwise use the entity history endpoint
        url = `${API_URL}/entity/history/${encodeURIComponent(entityName)}`;
        if (entityType) {
          url += `?entity_type=${encodeURIComponent(entityType)}`;
        }
      }

      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch history: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (transactionId) {
        // If we fetched from transaction endpoint, data is already the history object
        setHistoryData({
          status: 'success',
          data: data[entityName] || {}
        });
      } else {
        // If we fetched from entity endpoint, data is the history response
        setHistoryData(data);
      }
    } catch (error) {
      console.error('Error fetching entity history:', error);
      setError(error instanceof Error ? error.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return dateString;
    }
  };

  if (loading) {
    return (
      <Card withBorder p="md" radius="md">
        <Flex align="center" gap="md">
          <ThemeIcon size="lg" radius="md" color="blue" variant="light">
            <IconHistory size={18} />
          </ThemeIcon>
          <Text fw={500}>Entity History</Text>
        </Flex>
        <Flex justify="center" align="center" direction="column" p="xl" gap="md">
          <Loader size="sm" />
          <Text size="sm" c="dimmed">Loading history data...</Text>
        </Flex>
      </Card>
    );
  }

  if (error) {
    return (
      <Card withBorder p="md" radius="md">
        <Flex align="center" gap="md" mb="md">
          <ThemeIcon size="lg" radius="md" color="blue" variant="light">
            <IconHistory size={18} />
          </ThemeIcon>
          <Text fw={500}>Entity History</Text>
        </Flex>
        <Alert icon={<IconAlertCircle size={16} />} color="red" title="Error" radius="md">
          <Text size="sm">{error}</Text>
        </Alert>
      </Card>
    );
  }

  if (!historyData || historyData.status !== 'success' || !historyData.data) {
    return (
      <Card withBorder p="md" radius="md">
        <Flex align="center" gap="md" mb="md">
          <ThemeIcon size="lg" radius="md" color="blue" variant="light">
            <IconHistory size={18} />
          </ThemeIcon>
          <Text fw={500}>Entity History</Text>
        </Flex>
        <Alert icon={<IconInfoCircle size={16} />} color="blue" title="No History Found" radius="md">
          <Text size="sm">
            {historyData?.message || 'No historical data found for this entity.'}
          </Text>
        </Alert>
      </Card>
    );
  }

  const data = historyData.data;
  const orgData = data.organization;
  const personData = data.person;
  const entityData = orgData || personData;

  if (!entityData) {
    return (
      <Card withBorder p="md" radius="md">
        <Flex align="center" gap="md" mb="md">
          <ThemeIcon size="lg" radius="md" color="blue" variant="light">
            <IconHistory size={18} />
          </ThemeIcon>
          <Text fw={500}>Entity History</Text>
        </Flex>
        <Alert icon={<IconInfoCircle size={16} />} color="blue" title="No History Found" radius="md">
          <Text size="sm">No historical data found for this entity.</Text>
        </Alert>
      </Card>
    );
  }

  // Helper function to get risk color
  const getRiskColor = (score: number) => {
    if (score >= 0.7) return 'red';
    if (score >= 0.4) return 'orange';
    return 'green';
  };

  return (
    <Card withBorder p="lg" radius="md" className="scale-in">
      <Flex align="center" gap="md" mb="md">
        <ThemeIcon size="lg" radius="md" color="blue" variant="light">
          <IconHistory size={18} />
        </ThemeIcon>
        <Text fw={500}>Historical Profile</Text>
        <Badge color="blue" ml="auto">
          {entityData.transaction_count} Previous Transaction{entityData.transaction_count !== 1 ? 's' : ''}
        </Badge>
      </Flex>

      <Grid>
        <Grid.Col span={6}>
          <Paper withBorder p="md" radius="md">
            <Text size="xs" c="dimmed" tt="uppercase">First Seen</Text>
            <Flex align="center" gap="xs">
              <IconCalendarStats size={16} color={theme.colors.gray[6]} />
              <Text fw={500}>{formatDate(entityData.first_seen)}</Text>
            </Flex>
          </Paper>
        </Grid.Col>
        <Grid.Col span={6}>
          <Paper withBorder p="md" radius="md">
            <Text size="xs" c="dimmed" tt="uppercase">Last Seen</Text>
            <Flex align="center" gap="xs">
              <IconCalendarStats size={16} color={theme.colors.gray[6]} />
              <Text fw={500}>{formatDate(entityData.last_seen)}</Text>
            </Flex>
          </Paper>
        </Grid.Col>
      </Grid>

      <Card withBorder p="md" radius="md" mt="md">
        <Text fw={500} mb="md">Risk Profile History</Text>
        <Group justify="space-evenly" mb="md">
          <Flex direction="column" align="center">
            <Text size="xs" c="dimmed" mb={4}>Average Risk</Text>
            <RingProgress
              size={80}
              thickness={8}
              roundCaps
              sections={[{
                value: entityData.avg_risk_score * 100,
                color: getRiskColor(entityData.avg_risk_score),
              }]}
              label={
                <Center>
                  <Text fw={700} size="xs">{Math.round(entityData.avg_risk_score * 100)}%</Text>
                </Center>
              }
            />
          </Flex>
          
          <Flex direction="column" align="center">
            <Text size="xs" c="dimmed" mb={4}>Highest Risk</Text>
            <RingProgress
              size={80}
              thickness={8}
              roundCaps
              sections={[{
                value: entityData.max_risk_score * 100,
                color: getRiskColor(entityData.max_risk_score),
              }]}
              label={
                <Center>
                  <Text fw={700} size="xs">{Math.round(entityData.max_risk_score * 100)}%</Text>
                </Center>
              }
            />
          </Flex>
          
          <Flex direction="column" align="center">
            <Text size="xs" c="dimmed" mb={4}>Lowest Risk</Text>
            <RingProgress
              size={80}
              thickness={8}
              roundCaps
              sections={[{
                value: (entityData.min_risk_score || 0) * 100,
                color: getRiskColor(entityData.min_risk_score || 0),
              }]}
              label={
                <Center>
                  <Text fw={700} size="xs">{Math.round((entityData.min_risk_score || 0) * 100)}%</Text>
                </Center>
              }
            />
          </Flex>
        </Group>
        
        <Divider my="md" label={
          <Group gap="xs">
            <IconNetwork size={14} />
            <Text size="sm">Network Information</Text>
          </Group>
        } labelPosition="center" />
        
        <Accordion>
          {orgData && orgData.related_people && orgData.related_people.length > 0 && (
            <Accordion.Item value="related-people">
              <Accordion.Control icon={<IconUsers size={16} />}>
                <Text size="sm">Related People ({orgData.related_people.length})</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Role</th>
                      <th>Connected Since</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orgData.related_people.map((person, index) => (
                      <tr key={index}>
                        <td>{person.name}</td>
                        <td>
                          <Badge size="sm">{person.role}</Badge>
                        </td>
                        <td>{formatDate(person.since)}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Accordion.Panel>
            </Accordion.Item>
          )}
          
          {personData && personData.related_organizations && personData.related_organizations.length > 0 && (
            <Accordion.Item value="related-orgs">
              <Accordion.Control icon={<IconBuildingBank size={16} />}>
                <Text size="sm">Related Organizations ({personData.related_organizations.length})</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Table>
                  <thead>
                    <tr>
                      <th>Organization</th>
                      <th>Role</th>
                      <th>Connected Since</th>
                    </tr>
                  </thead>
                  <tbody>
                    {personData.related_organizations.map((org, index) => (
                      <tr key={index}>
                        <td>{org.name}</td>
                        <td>
                          <Badge size="sm">{org.role}</Badge>
                        </td>
                        <td>{formatDate(org.since)}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Accordion.Panel>
            </Accordion.Item>
          )}
          
          {entityData.transactions && entityData.transactions.length > 0 && (
            <Accordion.Item value="transactions">
              <Accordion.Control icon={<IconChartBar size={16} />}>
                <Text size="sm">Previous Transactions ({entityData.transactions.length})</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <Timeline active={entityData.transactions.length - 1} bulletSize={24} lineWidth={2}>
                  {entityData.transactions.map((txn, index) => (
                    <Timeline.Item key={index} bullet={<IconShield size={12} />} title={txn}>
                      <Text size="xs" mt={4}>Transaction ID: {txn}</Text>
                    </Timeline.Item>
                  ))}
                </Timeline>
              </Accordion.Panel>
            </Accordion.Item>
          )}
        </Accordion>
      </Card>
      
      <Flex justify="center" mt="sm">
        <Tooltip label={expanded ? "Show less" : "Show more details"}>
          <ActionIcon variant="subtle" onClick={toggle}>
            <IconChevronRight size={16} style={{
              transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s ease'
            }} />
          </ActionIcon>
        </Tooltip>
      </Flex>
      
      <Collapse in={expanded}>
        <Card withBorder p="md" radius="md" mt="md">
          <Text fw={500} mb="md">Entity Properties</Text>
          <ScrollArea h={200}>
            <Table>
              <thead>
                <tr>
                  <th>Property</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {entityData.properties && Object.entries(entityData.properties).map(([key, value]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>{value ? String(value) : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </ScrollArea>
        </Card>
      </Collapse>
    </Card>
  );
};

export default EntityHistory;