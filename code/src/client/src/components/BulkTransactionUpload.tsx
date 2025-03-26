import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Text, Title, Button, Group, Stack, Paper, Flex, Box,
    Tabs, Textarea, FileInput, SegmentedControl, Badge,
    Switch, Alert, Card, Progress, Divider, ThemeIcon,
    Code, ScrollArea, Table, LoadingOverlay, Tooltip,
    Accordion, useMantineTheme, rem
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useDisclosure } from '@mantine/hooks';
import {
    IconFileUpload, IconCheck, IconX, IconAlertCircle,
    IconCloudUpload, IconFileText, IconFileSpreadsheet,
    IconRefresh, IconDatabase, IconArrowRight, IconList,
    IconArrowBack, IconFileImport, IconChevronRight,
    IconInfoCircle, IconReload
} from '@tabler/icons-react';
import axios from 'axios';
import { API_URL } from '../api/constants';

const BulkTransactionUpload = () => {
    const [uploadType, setUploadType] = useState<'file' | 'paste'>('file');
    const [fileFormat, setFileFormat] = useState<'csv' | 'txt'>('txt');
    const [file, setFile] = useState<File | null>(null);
    const [pasteContent, setPasteContent] = useState('');
    const [uploadProgress, setUploadProgress] = useState(0);
    const [uploading, setUploading] = useState(false);
    const [waitForResults, setWaitForResults] = useState(false);
    const [processingResults, setProcessingResults] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [opened, { open, close }] = useDisclosure(false);

    const navigate = useNavigate();
    const theme = useMantineTheme();
    const fileInputRef = useRef<HTMLButtonElement>(null);

    const handleSubmit = async () => {
        try {
            // Validate input
            if (uploadType === 'file' && !file) {
                notifications.show({
                    title: 'Error',
                    message: 'Please select a file to upload',
                    color: 'red',
                });
                return;
            }

            if (uploadType === 'paste' && !pasteContent.trim()) {
                notifications.show({
                    title: 'Error',
                    message: 'Please enter transaction data',
                    color: 'red',
                });
                return;
            }

            setUploading(true);
            setError(null);
            setUploadProgress(10);

            // Prepare the data to send
            let dataToSend: string;

            if (uploadType === 'file') {
                dataToSend = await readFileAsText(file as File);
            } else {
                dataToSend = pasteContent;
            }

            // Set up axios request with upload progress tracking
            const formData = new FormData();
            const endpoint = `${API_URL}/transactions/bulk?file_format=${fileFormat}&wait=${waitForResults}`;

            setUploadProgress(30);

            // Send POST request
            const response = await axios.post(endpoint, dataToSend, {
                headers: {
                    'Content-Type': 'text/plain',
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 100));
                    setUploadProgress(30 + (percentCompleted * 0.5)); // Scale to 30-80% of our progress bar
                },
            });

            setUploadProgress(100);
            setProcessingResults(response.data);

            // Show success notification
            notifications.show({
                title: 'Upload Successful',
                message: `Processed ${response.data.processed} of ${response.data.total} transactions`,
                color: 'green',
                icon: <IconCheck size={16} />,
            });

            // Open results dialog
            open();
        } catch (err: any) {
            console.error('Error uploading transactions:', err);
            setError(err.response?.data?.detail || err.message || 'An unknown error occurred');

            notifications.show({
                title: 'Upload Failed',
                message: err.response?.data?.detail || err.message || 'An unknown error occurred',
                color: 'red',
                icon: <IconX size={16} />,
            });
        } finally {
            setUploading(false);
        }
    };

    const readFileAsText = (file: File): Promise<string> => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target?.result as string);
            reader.onerror = (e) => reject(new Error('Error reading file'));
            reader.readAsText(file);
        });
    };

    const handleViewResult = (transactionId: string) => {
        navigate(`/results/${transactionId}`);
        close();
    };

    const handleReset = () => {
        setFile(null);
        setPasteContent('');
        setProcessingResults(null);
        setError(null);
        setUploadProgress(0);
    };

    // Examples of the expected formats
    const csvExample = `Transaction ID,Date,Sender.Name,Sender.Account,Receiver.Name,Receiver.Account,Amount,Currency
TXN001,2023-08-15,Acme Corp,123456789,Global Ventures,987654321,50000,USD
TXN002,2023-08-16,Global Health,456789123,Medical Supplies Inc,321654987,75000,EUR`;

    const txtExample = `Transaction ID: TXN-2023-5A9B
Date: 2023-08-15 14:22:00
Sender:
Name: "Global Horizons Consulting LLC"
Account: IBAN CH56 0483 5012 3456 78009
Address: Rue du Marché 17, Geneva, Switzerland
Receiver:
Name: "Bright Future Nonprofit Inc"
Account: 987654321
Address: P.O. Box 1234, George Town, Cayman Islands
Amount: $49,850.00 (USD)
Transaction Type: Wire Transfer
Reference: "Charitable Donation Ref #DR-2023-0815"
---
Transaction ID: TXN-2023-7C2D
Date: 2023-08-16 10:15:00
Sender:
Name: "Quantum Holdings Ltd"
Account: VGB2BVIR024987654321
Receiver:
Name: "Golden Sands Trading FZE"
Account: AE450330000012345678901
Amount: $950,000.00 (USD)
Transaction Type: SWIFT`;

    return (
        <div style={{ position: 'relative' }}>
            <LoadingOverlay visible={uploading} />

            <Paper withBorder p="xl" radius="md" shadow="sm" mb="xl">
                <Flex align="center" justify="space-between" mb="xl">
                    <Box>
                        <Title order={2}>Bulk Transaction Upload</Title>
                        <Text c="dimmed" size="sm">Upload multiple transactions at once for batch processing</Text>
                    </Box>

                    <Badge size="lg" radius="md" variant="gradient" gradient={{ from: 'indigo', to: 'cyan' }}>
                        Batch Processing
                    </Badge>
                </Flex>

                <Tabs defaultValue="upload" radius="md">
                    <Tabs.List grow mb="md">
                        <Tabs.Tab
                            value="upload"
                            leftSection={<IconFileUpload size={16} />}
                            fw={500}
                        >
                            Upload Transactions
                        </Tabs.Tab>
                        <Tabs.Tab
                            value="format"
                            leftSection={<IconInfoCircle size={16} />}
                            fw={500}
                        >
                            Format Guidelines
                        </Tabs.Tab>
                    </Tabs.List>

                    <Tabs.Panel value="upload" pt="md">
                        <Stack>
                            <Flex gap="md" wrap="wrap">
                                <Box style={{ flexGrow: 1, minWidth: '250px' }}>
                                    <Text fw={500} mb="xs">Upload Method</Text>
                                    <SegmentedControl
                                        value={uploadType}
                                        onChange={(value) => setUploadType(value as 'file' | 'paste')}
                                        data={[
                                            {
                                                value: 'file',
                                                label: (
                                                    <Group gap="xs">
                                                        <IconFileImport size={16} />
                                                        <Text>Upload File</Text>
                                                    </Group>
                                                )
                                            },
                                            {
                                                value: 'paste',
                                                label: (
                                                    <Group gap="xs">
                                                        <IconFileText size={16} />
                                                        <Text>Paste Content</Text>
                                                    </Group>
                                                )
                                            }
                                        ]}
                                        fullWidth
                                    />
                                </Box>

                                <Box style={{ flexGrow: 1, minWidth: '250px' }}>
                                    <Text fw={500} mb="xs">File Format</Text>
                                    <SegmentedControl
                                        value={fileFormat}
                                        onChange={(value) => setFileFormat(value as 'csv' | 'txt')}
                                        data={[
                                            {
                                                value: 'txt',
                                                label: (
                                                    <Group gap="xs">
                                                        <IconFileText size={16} />
                                                        <Text>Text Format (---)</Text>
                                                    </Group>
                                                )
                                            },
                                            {
                                                value: 'csv',
                                                label: (
                                                    <Group gap="xs">
                                                        <IconFileSpreadsheet size={16} />
                                                        <Text>CSV Format</Text>
                                                    </Group>
                                                )
                                            }
                                        ]}
                                        fullWidth
                                    />
                                </Box>
                            </Flex>

                            {uploadType === 'file' ? (
                                <Box my="md">
                                    <FileInput
                                        label="Upload Transaction File"
                                        placeholder={`Choose a ${fileFormat.toUpperCase()} file`}
                                        accept={fileFormat === 'csv' ? '.csv' : '.txt'}
                                        value={file}
                                        onChange={setFile}
                                        clearable
                                        ref={fileInputRef}
                                        leftSection={<IconCloudUpload size={rem(14)} />}
                                        description={`Select a ${fileFormat.toUpperCase()} file containing multiple transactions`}
                                    />
                                </Box>
                            ) : (
                                <Box my="md">
                                    <Textarea
                                        label="Paste Transaction Data"
                                        placeholder={`Paste your ${fileFormat === 'csv' ? 'CSV content' : 'transactions separated by ---'}`}
                                        minRows={10}
                                        maxRows={20}
                                        value={pasteContent}
                                        onChange={(e) => setPasteContent(e.currentTarget.value)}
                                        autosize
                                        description={fileFormat === 'csv'
                                            ? "CSV format with header row"
                                            : "Text format with transactions separated by '---'"}
                                    />
                                </Box>
                            )}

                            <Switch
                                label="Wait for processing to complete"
                                description="Enable to wait for all transactions to be processed (may take longer)"
                                checked={waitForResults}
                                onChange={(event) => setWaitForResults(event.currentTarget.checked)}
                                my="md"
                            />

                            {error && (
                                <Alert
                                    icon={<IconAlertCircle size={16} />}
                                    title="Error"
                                    color="red"
                                    variant="filled"
                                >
                                    {error}
                                </Alert>
                            )}

                            {uploadProgress > 0 && uploadProgress < 100 && (
                                <Box my="md">
                                    <Text size="sm" mb="xs">Uploading transactions...</Text>
                                    <Progress
                                        value={uploadProgress}
                                        size="md"
                                        radius="xl"
                                        color={theme.primaryColor}
                                        striped
                                        animated
                                    />
                                </Box>
                            )}

                            <Group mt="md" justify="space-between">
                                <Button
                                    variant="light"
                                    onClick={() => navigate('/submit')}
                                    leftSection={<IconArrowBack size={16} />}
                                >
                                    Back to Single Upload
                                </Button>

                                <Group>
                                    <Button
                                        variant="outline"
                                        onClick={handleReset}
                                        disabled={uploading}
                                        leftSection={<IconRefresh size={16} />}
                                    >
                                        Reset
                                    </Button>
                                    <Button
                                        onClick={handleSubmit}
                                        disabled={uploading || (uploadType === 'file' && !file) || (uploadType === 'paste' && !pasteContent.trim())}
                                        loading={uploading}
                                        leftSection={<IconFileUpload size={16} />}
                                        variant="gradient"
                                        gradient={{ from: 'indigo', to: 'cyan' }}
                                    >
                                        Upload Transactions
                                    </Button>
                                </Group>
                            </Group>
                        </Stack>
                    </Tabs.Panel>

                    <Tabs.Panel value="format" pt="md">
                        <Accordion defaultValue="txt">
                            <Accordion.Item value="txt">
                                <Accordion.Control icon={<IconFileText size={16} />}>
                                    <Text fw={500}>Text Format (.txt)</Text>
                                </Accordion.Control>
                                <Accordion.Panel>
                                    <Text mb="md">
                                        For text format, each transaction should be separated by three dashes (---).
                                        Each transaction follows the standard format with fields like Transaction ID, Date, Sender/Receiver details, etc.
                                    </Text>

                                    <Paper withBorder p="md" bg="gray.0" mb="md">
                                        <Text fw={500} mb="xs">Example Text Format:</Text>
                                        <ScrollArea h={200} type="auto">
                                            <Code block>
                                                {txtExample}
                                            </Code>
                                        </ScrollArea>
                                    </Paper>

                                    <Alert icon={<IconInfoCircle size={16} />} color="blue">
                                        Use the separator "---" on a new line between each transaction in your text file.
                                    </Alert>
                                </Accordion.Panel>
                            </Accordion.Item>

                            <Accordion.Item value="csv">
                                <Accordion.Control icon={<IconFileSpreadsheet size={16} />}>
                                    <Text fw={500}>CSV Format (.csv)</Text>
                                </Accordion.Control>
                                <Accordion.Panel>
                                    <Text mb="md">
                                        CSV format requires a header row with specific column names. Sender and Receiver details should be prefixed with "Sender." and "Receiver."
                                    </Text>

                                    <Paper withBorder p="md" bg="gray.0" mb="md">
                                        <Text fw={500} mb="xs">Example CSV Format:</Text>
                                        <ScrollArea h={150} type="auto">
                                            <Code block>
                                                {csvExample}
                                            </Code>
                                        </ScrollArea>
                                    </Paper>

                                    <Alert icon={<IconInfoCircle size={16} />} color="blue">
                                        <Text fw={500} mb="xs">Required CSV Headers:</Text>
                                        <Text size="sm">
                                            Transaction ID, Date, Sender.Name, Receiver.Name, Amount, Currency
                                        </Text>
                                        <Text size="sm" mt="xs">
                                            Additional fields should be prefixed with "Sender." or "Receiver." (e.g., Sender.Account, Receiver.Address)
                                        </Text>
                                    </Alert>
                                </Accordion.Panel>
                            </Accordion.Item>
                        </Accordion>
                    </Tabs.Panel>
                </Tabs>
            </Paper>

            {/* Results Modal (implemented as expandable section when results are available) */}
            {processingResults && (
                <Paper withBorder p="xl" radius="md" shadow="sm" mb="xl">
                    <Flex justify="space-between" align="center" mb="lg">
                        <Box>
                            <Title order={4}>Bulk Upload Results</Title>
                            <Text c="dimmed" size="sm">
                                Processed {processingResults.processed} of {processingResults.total} transactions
                            </Text>
                        </Box>

                        <Group>
                            <Badge color="green" size="lg">
                                {processingResults.processed} Processed
                            </Badge>

                            {processingResults.failed > 0 && (
                                <Badge color="red" size="lg">
                                    {processingResults.failed} Failed
                                </Badge>
                            )}
                        </Group>
                    </Flex>

                    <Divider my="md" />

                    <ScrollArea h={400} type="auto">
                        <Table striped highlightOnHover withTableBorder>
                            <Table.Thead>
                                <Table.Tr>
                                    <Table.Th>Index</Table.Th>
                                    <Table.Th>Transaction ID</Table.Th>
                                    <Table.Th>Status</Table.Th>
                                    {waitForResults && <Table.Th>Risk Score</Table.Th>}
                                    <Table.Th>Actions</Table.Th>
                                </Table.Tr>
                            </Table.Thead>
                            <Table.Tbody>
                                {processingResults.results.map((result: any) => (
                                    <Table.Tr key={result.transaction_id}>
                                        <Table.Td>{result.index + 1}</Table.Td>
                                        <Table.Td>
                                            <Text fw={500}>{result.transaction_id}</Text>
                                        </Table.Td>
                                        <Table.Td>
                                            <Badge
                                                color={result.status === 'completed' ? 'green' : 'blue'}
                                                variant="filled"
                                            >
                                                {result.status}
                                            </Badge>
                                        </Table.Td>
                                        {waitForResults && (
                                            <Table.Td>
                                                {result.risk_score !== undefined ? (
                                                    <Badge
                                                        color={
                                                            result.risk_score >= 0.7 ? 'red' :
                                                                result.risk_score >= 0.4 ? 'orange' : 'green'
                                                        }
                                                    >
                                                        {Math.round(result.risk_score * 100)}%
                                                    </Badge>
                                                ) : (
                                                    <Text size="sm">-</Text>
                                                )}
                                            </Table.Td>
                                        )}
                                        <Table.Td>
                                            <Button
                                                variant="light"
                                                size="xs"
                                                onClick={() => handleViewResult(result.transaction_id)}
                                                rightSection={<IconChevronRight size={14} />}
                                            >
                                                View
                                            </Button>
                                        </Table.Td>
                                    </Table.Tr>
                                ))}

                                {processingResults.failures.map((failure: any) => (
                                    <Table.Tr key={`failure-${failure.index}`}>
                                        <Table.Td>{failure.index + 1}</Table.Td>
                                        <Table.Td>
                                            {failure.transaction_id ? (
                                                <Text fw={500}>{failure.transaction_id}</Text>
                                            ) : (
                                                <Text c="dimmed" fs="italic">Not assigned</Text>
                                            )}
                                        </Table.Td>
                                        <Table.Td>
                                            <Badge color="red" variant="filled">
                                                {failure.status || 'Failed'}
                                            </Badge>
                                        </Table.Td>
                                        {waitForResults && (
                                            <Table.Td>
                                                <Text size="sm">-</Text>
                                            </Table.Td>
                                        )}
                                        <Table.Td>
                                            <Tooltip label={failure.error || 'Unknown error'}>
                                                <Button
                                                    variant="subtle"
                                                    size="xs"
                                                    color="red"
                                                    disabled
                                                    leftSection={<IconAlertCircle size={14} />}
                                                >
                                                    Error
                                                </Button>
                                            </Tooltip>
                                        </Table.Td>
                                    </Table.Tr>
                                ))}
                            </Table.Tbody>
                        </Table>
                    </ScrollArea>

                    <Group justify="right" mt="xl">
                        <Button
                            onClick={handleReset}
                            leftSection={<IconReload size={16} />}
                            variant="light"
                        >
                            Upload More Transactions
                        </Button>
                        <Button
                            onClick={() => navigate('/')}
                            variant="filled"
                            rightSection={<IconArrowRight size={16} />}
                        >
                            Back to Dashboard
                        </Button>
                    </Group>
                </Paper>
            )}

            <Paper withBorder radius="md" shadow="sm" p="lg" mb="xl">
                <Flex align="center" gap="md" mb="lg">
                    <ThemeIcon size={36} radius="md" variant="light" color="blue">
                        <IconDatabase size={20} />
                    </ThemeIcon>
                    <Box>
                        <Title order={4}>Bulk Processing Guide</Title>
                        <Text size="sm" c="dimmed">Tips for effectively processing multiple transactions</Text>
                    </Box>
                </Flex>

                <Divider my="md" />

                <Stack gap="md">
                    <Card withBorder p="md" radius="md">
                        <Flex gap="md">
                            <ThemeIcon
                                size="lg"
                                radius="md"
                                color="indigo"
                                variant="light"
                            >
                                <IconList size={16} />
                            </ThemeIcon>
                            <Text fw={500}>Organize your transactions in a standardized format</Text>
                        </Flex>
                        <Text size="sm" mt="xs">
                            Whether using CSV or text format, ensure consistent fields and formatting for all transactions.
                        </Text>
                    </Card>

                    <Card withBorder p="md" radius="md">
                        <Flex gap="md">
                            <ThemeIcon
                                size="lg"
                                radius="md"
                                color="indigo"
                                variant="light"
                            >
                                <IconList size={16} />
                            </ThemeIcon>
                            <Text fw={500}>For large batches, consider processing asynchronously</Text>
                        </Flex>
                        <Text size="sm" mt="xs">
                            Turn off "Wait for processing" for faster response with large batches. You can check results later.
                        </Text>
                    </Card>

                    <Card withBorder p="md" radius="md">
                        <Flex gap="md">
                            <ThemeIcon
                                size="lg"
                                radius="md"
                                color="indigo"
                                variant="light"
                            >
                                <IconList size={16} />
                            </ThemeIcon>
                            <Text fw={500}>Review the processing results for each transaction</Text>
                        </Flex>
                        <Text size="sm" mt="xs">
                            After uploading, check the results table to ensure all transactions were processed correctly.
                        </Text>
                    </Card>
                </Stack>
            </Paper>
        </div>
    );
}
export default BulkTransactionUpload;