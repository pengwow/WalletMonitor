import { useState, useEffect } from 'react';

// 区块链交互hook
export const useBlockchain = (chain: string) => {
  const [blockNumber, setBlockNumber] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBlockNumber = async () => {
      setLoading(true);
      try {
        // 这里应该调用后端API获取区块号
        // 暂时使用模拟数据
        setTimeout(() => {
          setBlockNumber(1000000);
          setLoading(false);
        }, 1000);
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

// 钱包余额hook
export const useWalletBalance = (address: string, chain: string) => {
  const [balance, setBalance] = useState<string>('0');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBalance = async () => {
      if (!address || !chain) return;

      setLoading(true);
      try {
        // 这里应该调用后端API获取钱包余额
        // 暂时使用模拟数据
        setTimeout(() => {
          setBalance('1.23');
          setLoading(false);
        }, 1000);
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
