export const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);

export const formatNumber = (value: number) => new Intl.NumberFormat('en-IN').format(value);

export const formatPct = (value: number) => `${value.toFixed(value % 1 === 0 ? 0 : 1)}%`;
