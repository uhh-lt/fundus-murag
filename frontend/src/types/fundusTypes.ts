/**
 * TypeScript interfaces corresponding to the Pydantic models from fundus_murag/data/dtos/fundus.py
 */

export interface FundusCollectionContact {
  city: string;
  contact_name: string;
  department: string;
  email: string;
  institution: string;
  position: string;
  street: string;
  tel: string;
  www_department: string;
  www_name: string;
}
export interface FundusRecordField {
  name: string;
  label_en: string;
  label_de: string;
}

export interface FundusCollection {
  murag_id: string;
  collection_name: string;
  title: string;
  title_de: string;
  description: string;
  description_de: string;
  contacts: FundusCollectionContact[];
  title_fields: string[];
  fields: FundusRecordField[];
}

export interface FundusRecord {
  murag_id: string;
  title: string;
  fundus_id: number;
  catalogno: string;
  collection_name: string;
  image_name: string;
  details: Record<string, string>;
}

export interface FundusRecordImage {
  murag_id: string;
  fundus_id: number;
  image_name: string;
  base64_image: string;
}
