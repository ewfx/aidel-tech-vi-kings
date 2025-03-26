import { useState } from 'react';
import {
  Textarea, Button, Title, Paper, Text, Flex, Card,
  Alert, Divider, LoadingOverlay, Checkbox, Box,
  Stepper, Group, useMantineTheme, ThemeIcon,
  Code, Tabs, Collapse,
  Modal, Badge
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconFileUpload, IconAlertCircle, IconClock,
  IconInfoCircle, IconArrowRight, IconClipboard,
  IconCode, IconBrandTelegram, IconShieldCheck,
  IconDatabase, IconEye, IconCircleCheck,
  IconArrowBack, IconCheckbox, IconChevronRight, IconX,
  IconBriefcase, IconDeviceFloppy,
  IconUpload
} from '@tabler/icons-react';
import { useForm } from '@mantine/form';
import { useDisclosure } from '@mantine/hooks';
import { submitTransaction } from '../api/transactionApi';
import { Link } from 'react-router-dom';

const TransactionForm = () => {
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(0);
  const [sampleExpanded, setSampleExpanded] = useState(false);
  interface SubmissionResult {
    transaction_id?: string;
    run_id?: string;
    status?: string;
    risk_score?: number;
  }

  const [submissionResult, setSubmissionResult] = useState<SubmissionResult | null>(null);
  const [successModalOpened, { open: openSuccessModal, close: closeSuccessModal }] = useDisclosure(false);
  const theme = useMantineTheme();

  const form = useForm({
    initialValues: {
      transactionData: '',
      waitForCompletion: false,
    },
    validate: {
      transactionData: (value) => (value.trim().length > 0 ? null : 'Transaction data is required'),
    },
  });

  interface FormValues {
    transactionData: string;
    waitForCompletion: boolean;
  }

  interface SubmissionResponse {
    transaction_id?: string;
    run_id?: string;
    status?: string;
    risk_score?: number;
  }

  const handleSubmit = async (values: FormValues): Promise<void> => {
    try {
      setLoading(true);
      const response: SubmissionResponse = await submitTransaction(values.transactionData, values.waitForCompletion);

      // Store submission result
      setSubmissionResult(response);

      // Show success notification
      notifications.show({
        title: 'Transaction Submitted',
        message: values.waitForCompletion ?
          'Transaction has been successfully processed' :
          'Your transaction is being processed',
        color: 'green',
        icon: <IconCircleCheck size={16} />,
      });

      // Open success modal
      openSuccessModal();

    } catch (error) {
      console.error("Error submitting transaction:", error);
      notifications.show({
        title: 'Submission Error',
        message: 'Failed to submit transaction. Please try again.',
        color: 'red',
        icon: <IconAlertCircle size={16} />,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSampleData = () => {
    form.setFieldValue('transactionData', `
      Transaction ID: TEST-SANC-002
      Date: 2023-09-21 14:30:00

      Sender:
      Name: European Trade Solutions GmbH
      Account: DE89 3704 0044 0532 0130 00 (Deutsche Bank)
      Address: Friedrichstrasse 123, Berlin, Germany

      Receiver:
      Name: Sberbank of Russia
      Account: RU12 3456 7890 1234 5678 9012
      Address: Moscow, Russia

      Amount: $750,000 USD
      Transaction Type: SWIFT Transfer
      Reference: Equipment Purchase Contract #ER-789

      Additional Notes:
      Transfer related to energy sector equipment
      `);
  };

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(form.values.transactionData);
    notifications.show({
      title: 'Copied to clipboard',
      message: 'Transaction data has been copied to your clipboard',
      color: 'green',
    });
  };

  const handleViewResult = () => {
    if (submissionResult) {
      // Navigate to result page
      window.location.href = `/results/${submissionResult.transaction_id || submissionResult.run_id}`;
    }
  };

  const handleNewTransaction = () => {
    // Reset form and close modal
    form.reset();
    setActive(0);
    closeSuccessModal();
  };

  return (
    <div className="fade-in" style={{ position: 'relative' }}>
      <LoadingOverlay visible={loading} zIndex={1000} overlayProps={{ radius: "sm", blur: 2 }} />

      <Flex align="center" justify="space-between" mb="xl">
        <Box>
          <Title order={2} mb={4}>Submit Transaction</Title>
          <Text c="dimmed" size="sm">Enter transaction details for risk assessment</Text>
        </Box>

        <Group>
          <Badge size="lg" radius="md" variant="gradient" gradient={{ from: 'blue', to: 'cyan' }}>
            EIRA Processing
          </Badge>

          <Button
            component={Link}
            to="/bulk-upload"
            variant="light"
            rightSection={<IconUpload size={16} />}
          >
            Bulk Upload
          </Button>
        </Group>
      </Flex>

      <Paper withBorder radius="md" shadow="sm" p="xl" mb="xl">
        <Stepper
          active={active}
          onStepClick={setActive}
          size="md"
          color={theme.primaryColor}
          iconSize={42}
          mb="xl"
          allowNextStepsSelect={false}
        >
          <Stepper.Step
            label="Transaction Data"
            description="Enter transaction details"
            icon={<IconDatabase size={18} />}
            completedIcon={<IconCircleCheck size={18} />}
          >
            <Box>
              <Title order={4} mb="md">Enter Transaction Data</Title>

              <form onSubmit={form.onSubmit(() => setActive(1))}>
                <Box mb="md">
                  <Flex justify="space-between" mb="xs">
                    <Text fw={500} size="sm">Transaction Data</Text>
                    <Group>
                      <Button
                        variant="subtle"
                        size="xs"
                        onClick={handleSampleData}
                        leftSection={<IconInfoCircle size={16} />}
                        disabled={loading}
                      >
                        Use Sample Data
                      </Button>
                      <Button
                        variant="subtle"
                        size="xs"
                        onClick={handleCopyToClipboard}
                        disabled={!form.values.transactionData || loading}
                        leftSection={<IconClipboard size={16} />}
                      >
                        Copy
                      </Button>
                    </Group>
                  </Flex>

                  <Textarea
                    placeholder="Paste transaction data here..."
                    minRows={10}
                    maxRows={20}
                    autosize
                    radius="md"
                    {...form.getInputProps('transactionData')}
                    styles={{
                      input: {
                        fontFamily: 'monospace',
                        fontSize: '14px'
                      }
                    }}
                  />
                </Box>

                <Group justify="space-between" mt="xl">
                  <Button
                    variant="light"
                    onClick={() => window.location.href = '/'}
                    leftSection={<IconArrowBack size={16} />}
                    disabled={loading}
                  >
                    Back to Dashboard
                  </Button>

                  <Button
                    type="submit"
                    rightSection={<IconArrowRight size={16} />}
                    disabled={!form.values.transactionData.trim() || loading}
                    variant="gradient"
                    gradient={{ from: 'blue', to: 'cyan' }}
                  >
                    Continue
                  </Button>
                </Group>
              </form>
            </Box>

            <Card withBorder mt="xl" p="md" radius="md" shadow="xs">
              <Flex align="center" justify="space-between" mb="md">
                <Title order={5}>Transaction Data Format</Title>

                <Button
                  variant="subtle"
                  onClick={() => setSampleExpanded(!sampleExpanded)}
                  leftSection={sampleExpanded ? <IconEye size={16} /> : <IconCode size={16} />}
                  size="sm"
                >
                  {sampleExpanded ? "Hide Sample" : "View Sample Format"}
                </Button>
              </Flex>

              <Collapse in={sampleExpanded}>
                <Paper p="md" radius="md" withBorder bg="gray.0">
                  <Text fw={500} size="sm" mb="xs">Data Format Example:</Text>
                  <Code block style={{ whiteSpace: 'pre-wrap' }}>
                    {`Transaction ID: TXN-YYYY-XXXX
Date: YYYY-MM-DD HH:MM:SS
Sender:
Name: "Company or Individual Name"
Account: Account Number or IBAN
Address: Full Address
Notes: "Optional Notes"
Receiver:
Name: "Recipient Name"
Account: Account Number
Address: Recipient Address
Tax ID: Optional Tax ID
Amount: $X,XXX.XX (Currency)
Currency Exchange: Exchange details if applicable
Transaction Type: Wire Transfer, ACH, etc.
Reference: "Reference or Purpose"
Additional Notes:
"Any additional information about the transaction."
`}
                  </Code>
                </Paper>

                <Alert
                  icon={<IconInfoCircle size={16} />}
                  color="blue"
                  mt="md"
                  radius="md"
                >
                  The system will extract entities from this transaction data and perform risk analysis on them.
                </Alert>
              </Collapse>
            </Card>
          </Stepper.Step>

          <Stepper.Step
            label="Processing Options"
            description="Configure submission"
            icon={<IconBrandTelegram size={18} />}
            completedIcon={<IconCircleCheck size={18} />}
          >
            <Box>
              <Title order={4} mb="md">Processing Options</Title>

              <Alert
                icon={<IconClock size={18} />}
                title="Select Processing Mode"
                color="blue"
                variant="outline"
                mb="xl"
                radius="md"
              >
                Choose how you want to process this transaction. You can either wait for full results or be redirected immediately to track progress.
              </Alert>

              <Tabs defaultValue="async" variant="pills" mb="xl" radius="md">
                <Tabs.List grow mb="md">
                  <Tabs.Tab
                    value="async"
                    leftSection={<IconArrowRight size={16} />}
                    onClick={() => form.setFieldValue('waitForCompletion', false)}
                  >
                    Asynchronous (Default)
                  </Tabs.Tab>
                  <Tabs.Tab
                    value="sync"
                    leftSection={<IconCircleCheck size={16} />}
                    onClick={() => form.setFieldValue('waitForCompletion', true)}
                  >
                    Synchronous (Wait)
                  </Tabs.Tab>
                </Tabs.List>

                <Tabs.Panel value="async" pt="md">
                  <Card withBorder p="lg" bg={theme.colors.blue[0]} radius="md">
                    <Flex gap="md">
                      <ThemeIcon
                        size={52}
                        radius="xl"
                        variant="gradient"
                        gradient={{ from: 'blue', to: 'cyan' }}
                      >
                        <IconArrowRight size={24} />
                      </ThemeIcon>
                      <div>
                        <Text fw={500} size="lg" mb="xs">Asynchronous Processing</Text>
                        <Text size="sm">
                          Submit your transaction and be redirected immediately to the results page where you can track progress.
                          This option is best for large transactions that might take longer to process.
                        </Text>

                        <Group mt="md">
                          <ThemeIcon size="sm" radius="xl" color="green" variant="filled">
                            <IconCheckbox size={12} />
                          </ThemeIcon>
                          <Text size="sm">Immediate response</Text>
                        </Group>

                        <Group mt="xs">
                          <ThemeIcon size="sm" radius="xl" color="green" variant="filled">
                            <IconCheckbox size={12} />
                          </ThemeIcon>
                          <Text size="sm">Real-time progress tracking</Text>
                        </Group>

                        <Group mt="xs">
                          <ThemeIcon size="sm" radius="xl" color="green" variant="filled">
                            <IconCheckbox size={12} />
                          </ThemeIcon>
                          <Text size="sm">Suitable for complex transactions</Text>
                        </Group>
                      </div>
                    </Flex>
                    <Checkbox
                      mt="lg"
                      checked={!form.values.waitForCompletion}
                      onChange={() => form.setFieldValue('waitForCompletion', false)}
                      label="Don't wait for processing (redirect immediately)"
                      color={theme.primaryColor}
                      radius="sm"
                    />
                  </Card>
                </Tabs.Panel>

                <Tabs.Panel value="sync" pt="md">
                  <Card withBorder p="lg" bg={theme.colors.green[0]} radius="md">
                    <Flex gap="md">
                      <ThemeIcon
                        size={52}
                        radius="xl"
                        variant="gradient"
                        gradient={{ from: 'green', to: 'teal' }}
                      >
                        <IconCircleCheck size={24} />
                      </ThemeIcon>
                      <div>
                        <Text fw={500} size="lg" mb="xs">Synchronous Processing</Text>
                        <Text size="sm">
                          Wait for the transaction to be fully processed before being redirected to results.
                          This option works best for simple transactions that can be processed quickly.
                        </Text>

                        <Group mt="md">
                          <ThemeIcon size="sm" radius="xl" color="green" variant="filled">
                            <IconCheckbox size={12} />
                          </ThemeIcon>
                          <Text size="sm">Complete results immediately available</Text>
                        </Group>

                        <Group mt="xs">
                          <ThemeIcon size="sm" radius="xl" color="green" variant="filled">
                            <IconCheckbox size={12} />
                          </ThemeIcon>
                          <Text size="sm">Better for simple transactions</Text>
                        </Group>

                        <Group mt="xs">
                          <ThemeIcon size="sm" radius="xl" color="red" variant="filled">
                            <IconX size={12} />
                          </ThemeIcon>
                          <Text size="sm">May take longer for complex data</Text>
                        </Group>
                      </div>
                    </Flex>
                    <Checkbox
                      mt="lg"
                      checked={form.values.waitForCompletion}
                      onChange={() => form.setFieldValue('waitForCompletion', true)}
                      label="Wait for processing to complete (may take longer)"
                      color="green"
                      radius="sm"
                    />
                  </Card>
                </Tabs.Panel>
              </Tabs>

              <form onSubmit={form.onSubmit(handleSubmit)}>
                <Divider my="lg" />

                <Group justify="space-between">
                  <Button
                    variant="default"
                    onClick={() => setActive(0)}
                    leftSection={<IconArrowBack size={16} />}
                  >
                    Back
                  </Button>

                  <Group gap="sm">
                    <Button
                      variant="subtle"
                      onClick={() => form.reset()}
                      disabled={loading}
                      leftSection={<IconX size={16} />}
                    >
                      Reset
                    </Button>
                    <Button
                      type="submit"
                      leftSection={<IconFileUpload size={16} />}
                      loading={loading}
                      variant="gradient"
                      gradient={{ from: 'blue', to: 'cyan' }}
                      size="md"
                    >
                      Submit Transaction
                    </Button>
                  </Group>
                </Group>
              </form>
            </Box>
          </Stepper.Step>
        </Stepper>
      </Paper>

      <Paper withBorder radius="md" shadow="sm" p="lg" mb="xl">
        <Flex align="center" gap="md" mb="lg">
          <ThemeIcon size={36} radius="md" variant="light" color={theme.primaryColor}>
            <IconShieldCheck size={20} />
          </ThemeIcon>
          <Box>
            <Title order={4}>What Happens After Submission?</Title>
            <Text size="sm" c="dimmed">Our system will perform these steps automatically</Text>
          </Box>
        </Flex>

        <Box my="xl">
          <ProgressSteps />
        </Box>
      </Paper>

      {/* Success Modal */}
      <Modal
        opened={successModalOpened}
        onClose={closeSuccessModal}
        title={
          <Title order={4}>Transaction Submitted Successfully</Title>
        }
        centered
        size="lg"
        radius="md"
      >
        <Box>
          <Alert
            icon={<IconCircleCheck size={18} />}
            title="Your transaction has been received"
            color="green"
            radius="md"
            mb="md"
          >
            {form.values.waitForCompletion
              ? "Processing is complete. You can now view the detailed risk assessment."
              : "Your transaction is now being processed. You can track its progress on the results page."}
          </Alert>

          {submissionResult && (
            <Paper withBorder p="md" radius="md" mb="xl">
              <Text fw={500} mb="xs">Transaction Details:</Text>
              <Group mb="xs">
                <Text fw={500} size="sm">Transaction ID:</Text>
                <Text size="sm">{submissionResult.transaction_id || submissionResult.run_id}</Text>
              </Group>
              <Group mb="xs">
                <Text fw={500} size="sm">Status:</Text>
                <Badge
                  color={submissionResult.status === 'completed' ? 'green' : 'blue'}
                  variant="filled"
                >
                  {submissionResult.status || 'Processing'}
                </Badge>
              </Group>
              {submissionResult.risk_score !== undefined && (
                <Group>
                  <Text fw={500} size="sm">Risk Score:</Text>
                  <Badge
                    color={
                      submissionResult.risk_score >= 0.7 ? 'red' :
                        submissionResult.risk_score >= 0.4 ? 'orange' : 'green'
                    }
                    variant="filled"
                  >
                    {Math.round(submissionResult.risk_score * 100)}%
                  </Badge>
                </Group>
              )}
            </Paper>
          )}

          <Group justify="center" mt="xl">
            <Button
              variant="outline"
              onClick={handleNewTransaction}
              leftSection={<IconFileUpload size={16} />}
            >
              Submit Another Transaction
            </Button>
            <Button
              variant="gradient"
              gradient={{ from: 'blue', to: 'cyan' }}
              onClick={handleViewResult}
              rightSection={<IconChevronRight size={16} />}
            >
              View Results
            </Button>
          </Group>
        </Box>
      </Modal>
    </div>
  );
};

const ProgressSteps = () => {
  const steps = [
    {
      icon: <IconDatabase size={18} />,
      title: 'Entity Extraction',
      description: 'The system identifies organizations, individuals, and jurisdictions from your transaction.'
    },
    {
      icon: <IconShieldCheck size={18} />,
      title: 'Sanctions Screening',
      description: 'All entities are checked against global sanctions lists and PEP databases.'
    },
    {
      icon: <IconBriefcase size={18} />,
      title: 'Entity Verification',
      description: 'Organizations are verified through corporate registries and global databases.'
    },
    {
      icon: <IconAlertCircle size={18} />,
      title: 'Risk Assessment',
      description: 'A comprehensive risk score is calculated based on all findings and evidence.'
    },
    {
      icon: <IconDeviceFloppy size={18} />,
      title: 'Report Generation',
      description: 'A detailed risk report is generated with supporting evidence and recommendations.'
    },
  ];

  return (
    <Box>
      {steps.map((step, index) => (
        <Flex key={index} mb={index < steps.length - 1 ? "lg" : 0}>
          <Box mr="sm" mt={4}>
            <ThemeIcon
              size="lg"
              radius="xl"
              variant="light"
              color="blue"
              style={{
                position: 'relative',
                zIndex: 2
              }}
            >
              {step.icon}
            </ThemeIcon>

            {index < steps.length - 1 && (
              <Box
                style={{
                  position: 'absolute',
                  height: '50px',
                  width: '2px',
                  background: '#e9ecef',
                  marginLeft: '18px',
                  marginTop: '5px'
                }}
              />
            )}
          </Box>

          <Box>
            <Text fw={600} mb={4}>{step.title}</Text>
            <Text size="sm" c="dimmed">{step.description}</Text>
          </Box>
        </Flex>
      ))}
    </Box>
  );
};

export default TransactionForm;