// api/transactionApi.ts
import axios from 'axios';

// Configure the API URL based on environment
const API_URL = 'http://pradeep707.me:8000/api';

// Create an axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'text/plain',
  },
});

/**
 * Submit a new transaction for processing
 * @param transactionData - The raw transaction text data
 * @param waitForCompletion - Whether to wait for processing to complete
 * @returns The API response
 */
export const submitTransaction = async (transactionData: string, waitForCompletion: boolean = false) => {
  try {
    const response = await api.post(
      `/transaction${waitForCompletion ? '?wait=true' : ''}`,
      transactionData
    );
    return response.data;
  } catch (error) {
    console.error('Error submitting transaction:', error);
    throw error;
  }
};

/**
 * Get the status or result of a transaction
 * @param transactionId - The ID of the transaction to check
 * @returns The transaction status or result
 */
export const getTransactionStatus = async (transactionId: string) => {
  try {
    const response = await api.get(`/transaction/${transactionId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching transaction status for ${transactionId}:`, error);
    throw error;
  }
};

/**
 * Get the results of individual tasks for a transaction
 * @param transactionId - The ID of the transaction
 * @returns The task results
 */
export const getTaskResults = async (transactionId: string) => {
  try {
    const response = await api.get(`/transaction/${transactionId}/tasks`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching task results for ${transactionId}:`, error);
    throw error;
  }
};

/**
 * Fetch dashboard statistics
 * @returns Dashboard statistics
 */
export const fetchDashboardStats = async () => {
  try {
    const response = await api.get('/dashboard/stats');
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
  }
};

/**
 * Fetch transaction history
 * @returns List of transactions
 */
export const fetchTransactionHistory = async () => {
  try {
    const response = await api.get('/transactions');
    return response.data;
  } catch (error) {
    console.error('Error fetching transaction history:', error);
  }
};

// Add this function to client/src/api/transactionApi.ts

/**
 * Get the files available for a transaction
 * @param transactionId - The ID of the transaction
 * @returns List of files available for the transaction
 */
export const getTransactionFiles = async (transactionId: string) => {
  try {
    const response = await api.get(`/transaction/${transactionId}/files`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching files for transaction ${transactionId}:`, error);
    throw error;
  }
};