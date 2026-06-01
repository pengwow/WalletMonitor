import { useState, useEffect } from 'react';
import axios from 'axios';

export const useBlockchain = (chain: string) => {
  const [blockNumber, setBlockNumber] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBlockNumber = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`/api/transactions/stats/summary`);
        setBlockNumber(response.data.total_transactions || 0);
        setLoading(false);
      } catch (err) {
        setError('获取区块号失败');
        setLoading(false);
      }
    };

    fetchBlockNumber();
  }, [chain]);

  return {
    blockNumber,
    loading,
    error
  };
};

export const useWalletBalance = (address: string, chain: string) => {
  const [balance, setBalance] = useState<string>('0');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBalance = async () => {
      if (!address || !chain) return;

      setLoading(true);
      try {
        const wallets = await axios.get('/api/wallets');
        const wallet = wallets.data.find((w: any) => w.address === address && w.chain === chain);
        setBalance(wallet?.balance?.toString() || '0');
        setLoading(false);
      } catch (err) {
        setError('获取余额失败');
        setLoading(false);
      }
    };

    fetchBalance();
  }, [address, chain]);

  return {
    balance,
    loading,
    error
  };
};
