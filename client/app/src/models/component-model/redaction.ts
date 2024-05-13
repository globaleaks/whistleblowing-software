export interface RedactionData {
    id?:string;
    reference_id: string;
    internaltip_id: string;
    entry: string;
    operation?: string;
    content_type?: string;
    temporary_redaction?: any[];
    permanent_redaction?: any[];
}