import axios from 'axios';

export interface UsageResponse {
  success: boolean;
  message?: string;
  data?: {
    descriptions_generated_short?: number;
    descriptions_generated_long?: number;
    images_processed_sd?: number;
    images_processed_hd?: number;
    brand_voices_created?: number;
    brand_voice_edited?: number;
    analytics_reports_generated?: number;
    api_calls_made?: number;
    storage_used_mb?: number;
    [key: string]: any;
  };
  error?: string;
}

export async function getUsageStats(): Promise<UsageResponse> {
  const response = await axios.get<UsageResponse>('/usage/');
  return response.data;
}
