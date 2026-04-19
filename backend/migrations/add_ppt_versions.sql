-- 为 ppt_documents 表添加新字段
ALTER TABLE ppt_documents 
ADD COLUMN root_document_id INTEGER;

ALTER TABLE ppt_documents 
ADD COLUMN version_number INTEGER;

ALTER TABLE ppt_documents 
ADD COLUMN is_current BOOLEAN;

ALTER TABLE ppt_documents 
ADD COLUMN user_prompt VARCHAR;

-- 更新现有数据的初始值
UPDATE ppt_documents 
SET root_document_id = id,
    version_number = 1,
    is_current = 1,
    user_prompt = NULL;