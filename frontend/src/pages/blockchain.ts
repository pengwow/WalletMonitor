// 区块链相关工具函数

// 格式化地址（截取前后部分，中间用...代替）
export const formatAddress = (address: string, length: number = 4): string => {
  if (!address) return '';
  if (address.length <= length * 2 + 3) return address;
  return `${address.slice(0, length)}...${address.slice(-length)}`;
};

// 格式化金额（转换为合适的单位）
export const formatAmount = (amount: string | number, decimals: number = 18): string => {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  const formatted = numAmount / Math.pow(10, decimals);
  return formatted.toFixed(4);
};

// 格式化时间戳
export const formatTimestamp = (timestamp: number): string => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString();
};

// 验证钱包地址
export const validateAddress = (address: string, chain: string): boolean => {
  // 简单的地址验证，实际项目中应该使用更严格的验证
  if (chain === 'ethereum' || chain === 'bsc' || chain === 'polygon') {
    return /^0x[a-fA-F0-9]{40}$/.test(address);
  } else if (chain === 'solana') {
    return address.length === 44;
  }
  return false;
};

// 获取链的图标
export const getChainIcon = (chain: string): string => {
  const icons: Record<string, string> = {
    ethereum: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=ethereum%20logo%20icon&image_size=square',
    bsc: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=binance%20smart%20chain%20logo%20icon&image_size=square',
    solana: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=solana%20logo%20icon&image_size=square',
    polygon: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=polygon%20logo%20icon&image_size=square'
  };
  return icons[chain] || '';
};

// 获取风险等级的颜色
export const getRiskLevelColor = (level: string): string => {
  const colors: Record<string, string> = {
    high: 'red',
    medium: 'orange',
    low: 'blue'
  };
  return colors[level] || 'gray';
};
