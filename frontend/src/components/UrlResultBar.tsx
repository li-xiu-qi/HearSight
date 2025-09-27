import React from 'react';
import { Alert } from 'antd';
import type { ParseResult } from '../types';

interface UrlResultBarProps {
  urlError: string | null;
  urlResult: ParseResult | null;
  setUrlError: (error: string | null) => void;
  setUrlResult: (result: ParseResult | null) => void;
}

const UrlResultBar: React.FC<UrlResultBarProps> = ({
  urlError,
  urlResult,
  setUrlError,
  setUrlResult
}) => {
  if (!urlError && !urlResult) {
    return null;
  }

  return (
    <div className="url-result-bar">
      {urlError && <Alert type="error" message={urlError} showIcon closable onClose={() => setUrlError(null)} />}
      {urlResult && !('error' in urlResult) && (
        <Alert
          type="success"
          message={`解析成功：${urlResult.kind} - ${urlResult.id}`}
          showIcon
          closable
          onClose={() => setUrlResult(null)}
        />
      )}
    </div>
  );
};

export default UrlResultBar;