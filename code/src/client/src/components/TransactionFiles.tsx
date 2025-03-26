import React, { useState, useEffect } from 'react';
import {
  Text, Paper, Group, Flex, ThemeIcon,
  Badge, Loader, Button, Box,
  Alert, Divider, ActionIcon, ScrollArea,
  Title, Card, Tooltip, Modal, Code, Accordion,
  Tabs, useMantineTheme, TextInput, Transition, rgba
} from '@mantine/core';
import { useDisclosure, useHover } from '@mantine/hooks';
import {
  IconFolder, IconFile, IconFileAnalytics, IconRefresh, IconDownload, IconEye,
  IconAlertCircle, IconFolderOff, IconFileInfo,
  IconReportAnalytics, IconShieldCheck, IconBuildingBank, IconUser, IconAlertTriangle,
  IconNews, IconWorld, IconUserCheck, IconSearch, IconChevronRight,
  IconX, IconListTree,
  IconFileCode, IconFileTypeCsv,
  IconFileTypeXml, IconFileTypeTxt,
  IconInfoCircle
} from '@tabler/icons-react';

// Import API utilities
import { getTransactionFiles } from '../api/transactionApi';
import { API_URL } from '../api/constants';

// Define interfaces
interface FileData {
  name: string;
  display_name: string;
  description?: string;
  type: 'file' | 'directory';
  path: string;
  size?: number;
  content?: string;
  children?: FileData[];
}

interface TransactionFilesProps {
  transactionId: string;
  isProcessing: boolean;
}

// Helper function to format file size
const formatFileSize = (size: number) => {
  if (size < 1024) {
    return `${size} B`;
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  } else {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }
};

// Helper function to get the appropriate icon based on file/folder path
const getIcon = (item: FileData, size: number = 18) => {
  // For folders
  if (item.type === 'directory') {
    // Root level folders
    if (item.name === 'entity_data' || item.display_name === 'Entity Information')
      return <IconSearch size={size} stroke={1.5} />;
    if (item.name === 'risk_assessments' || item.display_name === 'Risk Assessments')
      return <IconShieldCheck size={size} stroke={1.5} />;
    if (item.name === 'analysis_reports' || item.display_name === 'Analysis Reports')
      return <IconReportAnalytics size={size} stroke={1.5} />;

    // Second level folders
    if (item.name === 'organization_results' || item.display_name === 'Organizations')
      return <IconBuildingBank size={size} stroke={1.5} />;
    if (item.name === 'people_results' || item.display_name === 'People')
      return <IconUser size={size} stroke={1.5} />;

    // Specific data folders
    if (item.name === 'opencorporates' || item.display_name === 'Corporate Registry')
      return <IconFileInfo size={size} stroke={1.5} />;
    if (item.name === 'sanctions' || item.display_name === 'Sanctions Screening')
      return <IconAlertTriangle size={size} stroke={1.5} />;
    if (item.name === 'wikidata' || item.display_name === 'Entity Network')
      return <IconWorld size={size} stroke={1.5} />;
    if (item.name === 'pep' || item.display_name === 'Politically Exposed Persons')
      return <IconUserCheck size={size} stroke={1.5} />;
    if (item.name === 'news' || item.display_name === 'Adverse Media')
      return <IconNews size={size} stroke={1.5} />;

    // Default folder icon
    return <IconFolder size={size} stroke={1.5} />;
  }

  // For files based on extension
  const ext = item.name.split('.').pop()?.toLowerCase();

  if (ext === 'json') {
    if (item.name.includes('risk_assessment'))
      return <IconShieldCheck size={size} stroke={1.5} />;
    if (item.name.includes('entity') || item.name.includes('entities'))
      return <IconSearch size={size} stroke={1.5} />;
    return <IconFileCode size={size} stroke={1.5} />;
  } else if (ext === 'txt') {
    return <IconFileTypeTxt size={size} stroke={1.5} />;
  } else if (ext === 'csv') {
    return <IconFileTypeCsv size={size} stroke={1.5} />;
  } else if (ext === 'xml') {
    return <IconFileTypeXml size={size} stroke={1.5} />;
  } else if (item.name.includes('result') || item.name.includes('assessment')) {
    return <IconFileAnalytics size={size} stroke={1.5} />;
  }

  // Default file icon
  return <IconFile size={size} stroke={1.5} />;
};

// File Card component for grid view
const FileCard: React.FC<{
  file: FileData;
  onView: (file: FileData) => void;
  onDownload: (file: FileData) => void;
}> = ({ file, onView, onDownload }) => {
  const theme = useMantineTheme();
  const { hovered, ref } = useHover();

  // Determine the card's background color based on the file type
  const getCardColor = () => {
    if (file.name.includes('risk')) return rgba(theme.colors.red[1], 0.7);
    if (file.name.includes('entity')) return rgba(theme.colors.blue[1], 0.7);
    if (file.name.includes('transaction')) return rgba(theme.colors.green[1], 0.7);
    return rgba(theme.colors.gray[1], 0.7);
  };

  return (
    <Card
      ref={ref}
      withBorder
      padding="md"
      radius="md"
      shadow={hovered ? "md" : "sm"}
      style={{
        transition: 'all 0.2s ease',
        transform: hovered ? 'translateY(-5px)' : 'none',
        backgroundColor: getCardColor(),
        cursor: 'pointer',
        position: 'relative',
        height: '100%'
      }}
      onClick={() => onView(file)}
    >
      <Flex direction="column" justify="space-between" h="100%">
        <Box>
          <Flex align="center" gap="sm" mb="sm">
            <ThemeIcon
              variant={hovered ? "filled" : "light"}
              size="md"
              radius="md"
              color="blue"
            >
              {getIcon(file, 18)}
            </ThemeIcon>
            <Text fw={500} lineClamp={1}>{file.display_name}</Text>
          </Flex>

          {file.size !== undefined && (
            <Badge size="sm" variant="outline" radius="sm">
              {formatFileSize(file.size)}
            </Badge>
          )}
        </Box>

        <Transition mounted={hovered} transition="fade" duration={200}>
          {(styles) => (
            <Group style={{ ...styles, justifyContent: 'flex-end' }}>
              <ActionIcon
                variant="light"
                color="blue"
                onClick={(e) => {
                  e.stopPropagation();
                  onView(file);
                }}
                radius="xl"
              >
                <IconEye size={16} />
              </ActionIcon>
              <ActionIcon
                variant="light"
                color="green"
                onClick={(e) => {
                  e.stopPropagation();
                  onDownload(file);
                }}
                radius="xl"
              >
                <IconDownload size={16} />
              </ActionIcon>
            </Group>
          )}
        </Transition>
      </Flex>
    </Card>
  );
};

// Tree View Item for a sleeker folder tree visualization
const TreeViewItem: React.FC<{
  item: FileData;
  onView: (file: FileData) => void;
  onDownload: (file: FileData) => void;
  level: number;
}> = ({ item, onView, onDownload, level }) => {
  const [expanded, setExpanded] = useState(level < 1);
  const { hovered, ref } = useHover();
  const theme = useMantineTheme();

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (item.type === 'directory') {
      setExpanded(!expanded);
    }
  };

  return (
    <Box>
      <Flex
        ref={ref}
        align="center"
        px="sm"
        py="xs"
        style={{
          borderRadius: theme.radius.sm,
          backgroundColor: hovered ? rgba(theme.colors.blue[1], 0.5) : 'transparent',
          cursor: 'pointer',
          marginLeft: `${level * 16}px`,
          transition: 'background-color 0.2s ease'
        }}
        onClick={toggleExpand}
      >
        {item.type === 'directory' && (
          <ActionIcon
            size="sm"
            variant="transparent"
            onClick={toggleExpand}
            style={{ transform: expanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s ease' }}
          >
            <IconChevronRight size={16} />
          </ActionIcon>
        )}

        <ThemeIcon
          size="sm"
          variant="light"
          color={item.type === 'directory' ? 'blue' : 'gray'}
          style={{ margin: '0 8px' }}
        >
          {getIcon(item, 14)}
        </ThemeIcon>

        <Text size="sm" style={{ flex: 1 }}>{item.display_name}</Text>

        {item.size !== undefined && (
          <Text size="xs" c="dimmed" mr="md">
            {formatFileSize(item.size)}
          </Text>
        )}

        {item.type === 'file' && hovered && (
          <Group gap="xs">
            <ActionIcon
              size="sm"
              variant="subtle"
              color="blue"
              onClick={(e) => {
                e.stopPropagation();
                onView(item);
              }}
            >
              <IconEye size={14} />
            </ActionIcon>
            <ActionIcon
              size="sm"
              variant="subtle"
              color="green"
              onClick={(e) => {
                e.stopPropagation();
                onDownload(item);
              }}
            >
              <IconDownload size={14} />
            </ActionIcon>
          </Group>
        )}
      </Flex>

      {item.type === 'directory' && expanded && item.children && (
        <Box>
          {item.children.map((child, index) => (
            <TreeViewItem
              key={`${child.path}-${index}`}
              item={child}
              onView={onView}
              onDownload={onDownload}
              level={level + 1}
            />
          ))}
        </Box>
      )}
    </Box>
  );
};

// Enhanced TransactionFiles component
const TransactionFiles: React.FC<TransactionFilesProps> = ({ transactionId, isProcessing }) => {
  const [files, setFiles] = useState<FileData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileData | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [viewType, setViewType] = useState<'grid' | 'tree'>('tree');
  const [searchQuery, setSearchQuery] = useState('');
  const [opened, { open, close }] = useDisclosure(false);
  const theme = useMantineTheme();

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const data = await getTransactionFiles(transactionId);
      setFiles(data);
      setError(null);
    } catch (err) {
      console.error("Error fetching transaction files:", err);
      setError("Failed to load transaction files. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
  }, [transactionId]);

  const handleViewFile = async (file: FileData) => {
    try {
      console.log("Fetching file content for:", file.path);
      // First set the selected file without content to show loading state
      setSelectedFile(file);
      setFileContent(null);
      setFileLoading(true);
      open();

      // Then fetch the file content
      const response = await fetch(`${API_URL}/transaction/${transactionId}/files/${file.path}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch file content: ${response.statusText}`);
      }

      const data = await response.json();
      setFileContent(data.content);
    } catch (error) {
      console.error("Error fetching file content:", error);
      setFileContent(`Error loading file content: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setFileLoading(false);
    }
  };

  const handleDownloadFile = (file: FileData) => {
    try {
      // Create download URL with the download flag
      const downloadUrl = `${API_URL}/transaction/${transactionId}/files/${file.path}?download=true`;

      // Open the download URL in a new tab/window
      window.open(downloadUrl, '_blank');
    } catch (error) {
      console.error("Error initiating download:", error);
      // Show an error notification
      alert(`Error downloading file: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  // Filter files based on search query
  const filterFilesBySearch = (items: FileData[]): FileData[] => {
    if (!searchQuery) return items;

    return items.flatMap(item => {
      // Check if the current item matches
      const matchesSearch =
        item.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.name.toLowerCase().includes(searchQuery.toLowerCase());

      if (item.type === 'file') {
        // Return the item if it matches, otherwise empty array (will be filtered out)
        return matchesSearch ? [item] : [];
      } else {
        // For directories, recursively filter children
        const filteredChildren = item.children ? filterFilesBySearch(item.children) : [];

        // Return the directory with filtered children if either:
        // 1. The directory itself matches the search
        // 2. Any of its children match the search
        if (matchesSearch || filteredChildren.length > 0) {
          return [{
            ...item,
            children: filteredChildren
          }];
        }

        // Directory and none of its children match, filter it out
        return [];
      }
    });
  };

  const filteredFiles = filterFilesBySearch(files);

  // Render files based on view type
  const renderFiles = () => {
    if (viewType === 'grid') {
      // Flatten the file structure for grid view
      const flattenFiles = (items: FileData[]): FileData[] => {
        return items.flatMap(item => {
          if (item.type === 'file') {
            return [item];
          } else {
            return item.children ? flattenFiles(item.children) : [];
          }
        });
      };

      const flatFiles = flattenFiles(filteredFiles);

      return (
        <Box p="md">
          <Group mb="lg" justify="apart">
            <Text fw={500}>Files ({flatFiles.length})</Text>
            <Badge>{viewType === 'grid' ? 'Grid View' : 'Tree View'}</Badge>
          </Group>

          {flatFiles.length > 0 ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: '16px'
            }}>
              {flatFiles.map((file, index) => (
                <FileCard
                  key={`${file.path}-${index}`}
                  file={file}
                  onView={handleViewFile}
                  onDownload={handleDownloadFile}
                />
              ))}
            </div>
          ) : (
            <Text ta="center" c="dimmed" py="xl">No files match your search</Text>
          )}
        </Box>
      );
    } else {
      // Tree view
      return (
        <Box p="md">
          <Group mb="lg" justify="apart">
            <Text fw={500}>File Explorer</Text>
            <Badge>{viewType === 'grid' ? 'Grid View' : 'Tree View'}</Badge>
          </Group>

          <Paper withBorder p="md" radius="md">
            <ScrollArea h={400} type="hover" offsetScrollbars>
              {filteredFiles.length > 0 ? (
                filteredFiles.map((item, index) => (
                  <TreeViewItem
                    key={`${item.path}-${index}`}
                    item={item}
                    onView={handleViewFile}
                    onDownload={handleDownloadFile}
                    level={0}
                  />
                ))
              ) : (
                <Text ta="center" c="dimmed" py="xl">No files match your search</Text>
              )}
            </ScrollArea>
          </Paper>
        </Box>
      );
    }
  };

  if (loading) {
    return (
      <Card withBorder p="xl" radius="md" shadow="sm">
        <Flex direction="column" align="center" gap="md" className="pulse">
          <Loader size="md" variant="dots" />
          <Text c="dimmed">Loading knowledge base files...</Text>
          <Text size="xs" c="dimmed" opacity={0.7}>This usually takes just a moment</Text>
        </Flex>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert
        icon={<IconAlertCircle size={16} />}
        title="Error loading knowledge base"
        color="red"
        variant="filled"
        radius="md"
      >
        <Text size="sm" mb="md">{error}</Text>
        <Button
          variant="white"
          leftSection={<IconRefresh size={16} />}
          onClick={fetchFiles}
          size="xs"
        >
          Try Again
        </Button>
      </Alert>
    );
  }

  return (
    <Card withBorder p="lg" radius="md" shadow="sm" className="frosted-card">
      <Tabs defaultValue="files" radius="md">
        <Tabs.List mb="md">
          <Tabs.Tab
            value="files"
            leftSection={<IconFolder size={16} />}
            fw={500}
          >
            Knowledge Base
          </Tabs.Tab>
          <Tabs.Tab
            value="info"
            leftSection={<IconInfoCircle size={16} />}
            fw={500}
          >
            About
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="files">
          <Flex justify="space-between" mb="md" wrap="wrap" gap="sm">
            <Flex align="center" gap="md">
              <ThemeIcon size="lg" radius="md" color="blue" variant="light">
                <IconReportAnalytics size={20} />
              </ThemeIcon>
              <Box>
                <Title order={5}>Knowledge Base</Title>
                <Text size="xs" c="dimmed">Transaction: {transactionId}</Text>
              </Box>
            </Flex>

            <Group>
              <Button
                variant="light"
                size="xs"
                leftSection={<IconRefresh size={16} />}
                onClick={fetchFiles}
                loading={loading}
              >
                Refresh
              </Button>

              <SegmentedButtons
                value={viewType}
                onChange={setViewType as (value: string) => void}
              />
            </Group>
          </Flex>

          <Divider mb="md" />

          <TextInput
            placeholder="Search files and folders..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.currentTarget.value)}
            leftSection={<IconSearch size={16} />}
            rightSection={
              searchQuery ? (
                <ActionIcon size="sm" onClick={() => setSearchQuery('')}>
                  <IconX size={14} />
                </ActionIcon>
              ) : null
            }
            mb="md"
          />

          {files.length > 0 ? (
            renderFiles()
          ) : (
            <Box py="xl">
              <Flex direction="column" align="center" gap="md">
                <ThemeIcon size={50} radius="xl" color="gray" variant="light">
                  <IconFolderOff size={24} />
                </ThemeIcon>
                <Text ta="center" fw={500}>No files available</Text>
                <Text size="sm" c="dimmed" ta="center" maw={400}>
                  {isProcessing ?
                    "The transaction is still being processed. Files will appear here once processing is complete." :
                    "No knowledge base files were found for this transaction."}
                </Text>
              </Flex>
            </Box>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="info">
          <Card withBorder radius="md" mb="md">
            <Title order={5} mb="md">About Knowledge Base</Title>
            <Text size="sm">
              The Knowledge Base contains all the supporting data and analytical reports that were used to generate the risk assessment. This includes:
            </Text>

            <Box my="md">
              <FileCategoryInfo />
            </Box>

            <Alert
              icon={<IconInfoCircle size={16} />}
              color="blue"
              variant="light"
              radius="md"
            >
              <Text size="sm">
                You can view or download any file by clicking on it. Files are organized in a structured hierarchy for easy navigation.
              </Text>
            </Alert>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* File content viewer modal */}
      <Modal
        opened={opened}
        onClose={close}
        title={
          <Flex align="center" gap="sm">
            <ThemeIcon size="md" radius="md" color="blue" variant="light">
              {selectedFile && getIcon(selectedFile)}
            </ThemeIcon>
            <Text fw={600}>{selectedFile?.display_name || "File Viewer"}</Text>
          </Flex>
        }
        size="xl"
        centered
        padding="lg"
        styles={{
          title: { fontWeight: 600 },
          header: { paddingBottom: theme.spacing.xs }
        }}
      >
        <Box>
          {selectedFile && (
            <Group justify="apart" mb="xs">
              <Text size="sm" c="dimmed">
                {selectedFile.path}
              </Text>
              {selectedFile.size && (
                <Badge size="sm" variant="outline">
                  {formatFileSize(selectedFile.size)}
                </Badge>
              )}
            </Group>
          )}

          <Divider mb="md" />

          {fileLoading ? (
            <Flex direction="column" align="center" py="xl" gap="md">
              <Loader size="sm" />
              <Text>Loading file content...</Text>
            </Flex>
          ) : (
            <ScrollArea h={400} type="auto" offsetScrollbars>
              <Code block style={{
                fontSize: '13px',
                lineHeight: 1.5,
                padding: '16px'
              }}>
                {fileContent}
              </Code>
            </ScrollArea>
          )}
        </Box>

        <Group justify="right" mt="md">
          <Button variant="light" onClick={close}>
            Close
          </Button>
          {selectedFile && (
            <Button onClick={() => handleDownloadFile(selectedFile)} leftSection={<IconDownload size={16} />}>
              Download
            </Button>
          )}
        </Group>
      </Modal>
    </Card>
  );
};

// Segmented buttons for view type switch
const SegmentedButtons: React.FC<{
  value: string;
  onChange: (value: string) => void;
}> = ({ value, onChange }) => {
  return (
    <Group gap={4}>
      <Tooltip label="Tree View">
        <ActionIcon
          variant={value === 'tree' ? 'filled' : 'subtle'}
          color={value === 'tree' ? 'blue' : 'gray'}
          onClick={() => onChange('tree')}
          size="md"
          radius="md"
        >
          <IconListTree size={16} />
        </ActionIcon>
      </Tooltip>

      <Tooltip label="Grid View">
        <ActionIcon
          variant={value === 'grid' ? 'filled' : 'subtle'}
          color={value === 'grid' ? 'blue' : 'gray'}
          onClick={() => onChange('grid')}
          size="md"
          radius="md"
        >
          <IconFileCode size={16} />
        </ActionIcon>
      </Tooltip>
    </Group>
  );
};

// File category information component
const FileCategoryInfo: React.FC = () => {
  return (
    <Accordion variant="contained" radius="md">
      <Accordion.Item value="entity-info">
        <Accordion.Control icon={<IconSearch size={16} />}>
          Entity Information
        </Accordion.Control>
        <Accordion.Panel>
          <Text size="sm">
            Detailed information about the organizations and individuals identified in the transaction, including corporate registry data, sanctions screening, and network analysis.
          </Text>
        </Accordion.Panel>
      </Accordion.Item>

      <Accordion.Item value="risk">
        <Accordion.Control icon={<IconShieldCheck size={16} />}>
          Risk Assessments
        </Accordion.Control>
        <Accordion.Panel>
          <Text size="sm">
            Comprehensive risk evaluation reports and supporting evidence used to determine the final risk score.
          </Text>
        </Accordion.Panel>
      </Accordion.Item>

      <Accordion.Item value="analysis">
        <Accordion.Control icon={<IconReportAnalytics size={16} />}>
          Analysis Reports
        </Accordion.Control>
        <Accordion.Panel>
          <Text size="sm">
            Detailed analysis of transaction patterns, entity relationships, and other factors that contributed to the risk assessment.
          </Text>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
};

export default TransactionFiles;