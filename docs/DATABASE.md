# IMAP MCP Server Database Design

## Overview

This document outlines the database caching strategy for the IMAP MCP server. The goal is to cache email analytics results and metadata in a Cloud Storage-backed SQLite database to improve performance and enable persistence across server restarts.

## Database Architecture

### Storage Layer

- SQLite database file stored in Google Cloud Storage
- Automatic sync between local and cloud storage
- Lock management to prevent concurrent writes
- Local caching with periodic cloud sync

### Schema Design

#### Processing State

```sql
CREATE TABLE processing_state (
    id INTEGER PRIMARY KEY,
    folder TEXT,
    last_message_id TEXT,
    last_processed_date TEXT,
    last_success INTEGER,  -- SQLite boolean
    error_message TEXT,
    sync_token TEXT       -- For IMAP servers that support it
);
```

#### Email Messages Cache

```sql
CREATE TABLE email_messages (
    id INTEGER PRIMARY KEY,
    message_id TEXT UNIQUE,
    folder TEXT,
    subject TEXT,
    sender TEXT,
    recipients TEXT,  -- JSON array
    date TEXT,
    thread_id TEXT,
    references TEXT,  -- JSON array
    content_preview TEXT,
    importance_score REAL,
    labels TEXT,      -- JSON array
    category TEXT,
    response_time REAL,
    last_updated TEXT
);
```

#### Thread Analysis Cache

```sql
CREATE TABLE email_threads (
    id INTEGER PRIMARY KEY,
    thread_id TEXT UNIQUE,
    subject TEXT,
    participants TEXT,  -- JSON array
    last_update TEXT,
    message_count INTEGER,
    average_response_time REAL,
    is_active INTEGER,  -- SQLite boolean
    importance_score REAL,
    category TEXT,
    labels TEXT        -- JSON array
);
```

#### Smart Folder Cache

```sql
CREATE TABLE smart_folders (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    rules TEXT,        -- JSON array
    created_at TEXT,
    last_applied TEXT,
    message_count INTEGER,
    is_active INTEGER  -- SQLite boolean
);
```

### Synchronization Strategy

1. Cloud Storage Integration

   - Database file stored in configured GCS bucket
   - Local working copy in .vscode/data/cache.db
   - Lock file in GCS to prevent concurrent writes

2. Sync Operations

   - Download latest DB on server start
   - Upload after significant changes
   - Periodic sync every N minutes
   - Handle conflicts with timestamp-based resolution

3. Locking Mechanism
   - Create lock file in GCS before writes
   - Include server ID and timestamp
   - Auto-expire locks after 5 minutes
   - Handle stale locks with force option

### Cache Invalidation

1. Time-based Expiration

   - Email metadata: 24 hours
   - Thread analysis: 12 hours
   - Smart folders: 48 hours

2. Event-based Invalidation
   - On message changes
   - On folder structure changes
   - When analysis parameters change

## Implementation Plan

### Phase 1: Basic Database Setup

1. Initialize SQLite schema
2. Set up GCS connection
3. Implement basic sync operations

### Phase 2: Cache Management

1. Add cache invalidation
2. Implement locking mechanism
3. Handle sync conflicts

### Phase 3: Optimization

1. Add batch operations
2. Implement query optimization
3. Add performance monitoring

## Safety Considerations

1. Data Security

   - No sensitive email content stored
   - Only metadata and analysis results
   - Encrypted storage in GCS

2. Error Handling

   - Graceful degradation on sync failures
   - Automatic recovery from corrupt cache
   - Transaction rollback support

3. Performance Guards
   - Maximum cache size limits
   - Automatic cleanup of old records
   - Query timeout limits

## Success Metrics

1. Cache hit rate
2. Sync success rate
3. Query response times
4. Storage space utilization
5. Error recovery rate
