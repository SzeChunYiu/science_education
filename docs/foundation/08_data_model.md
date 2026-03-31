# 8. Data Model

## Tables / Collections

### subjects
id, name, description

### modules
id, subject_id, name, ordering

### topics
id, module_id, slug, name, description, difficulty, historical_importance, visual_potential, platform_fit_score, status

### sources
id, topic_id, title, author, year, source_type, url_or_file_path, citation_text, trust_score

### research_dossiers
id, topic_id, version, json_payload, created_at

### episode_plans
id, topic_id, episode_number, objective, historical_context, analogy, key_claims, references, hook

### scripts
id, topic_id, episode_number, platform, version, content, status

### media_assets
id, topic_id, episode_number, platform, asset_type, file_path, status

### publication_jobs
id, topic_id, episode_number, platform, scheduled_at, published_at, remote_post_id, status, disclosure_flags

### analytics
id, publication_job_id, metric_name, metric_value, captured_at
