import { FundusCollection, FundusRecord, FundusRecordImage } from "../types/fundusTypes";

export const lookupService = {
  async getFundusRecord(muragId: string): Promise<FundusRecord> {
    const response = await fetch('/api/data/lookup/records?murag_id=' + muragId);
    if (!response.ok) {
      throw new Error('Failed to fetch Fundus Record');
    }
    return response.json();
  },
  async getFundusRecordImage(muragId: string): Promise<FundusRecordImage> {
    const response = await fetch('/api/data/lookup/records/image?murag_id=' + muragId);
    if (!response.ok) {
      throw new Error('Failed to fetch Fundus Record Image');
    }
    return response.json();
  },
  async getFundusCollection(muragId: string): Promise<FundusCollection> {
    const response = await fetch('/api/data/lookup/collections?murag_id=' + muragId);
    if (!response.ok) {
      throw new Error('Failed to fetch Fundus Collection');
    }
    return response.json();
  }
};

export default lookupService;
