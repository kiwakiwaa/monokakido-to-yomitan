#!/usr/bin/env python3
"""
NANMED20 Dictionary Extractor

Analyzes and extracts entries from ALL tables in the database.
Creates a simple JSON with each dictionary entry as a separate item.
"""

import sqlite3
import json
import argparse
import os
import sys
import time
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description='Comprehensive extraction of dictionary entries')
    parser.add_argument('--input', '-i', required=True, help='Path to the SQL database file')
    parser.add_argument('--output', '-o', default='dictionary.json', help='Output JSON file path')
    parser.add_argument('--separator', '-s', default='|', help='Separator for term and reading (default: |)')
    parser.add_argument('--pretty', '-p', action='store_true', help='Output pretty-printed JSON')
    parser.add_argument('--analyze', '-a', action='store_true', help='Only analyze database structure')
    parser.add_argument('--limit', '-l', type=int, help='Limit entries per table (for testing)')
    return parser.parse_args()

def check_for_css_patterns(cursor, tables):
    """Check for potential CSS content in the database."""
    print("\nLooking for potential CSS content...")
    
    # Tables that might contain CSS
    css_tables = []
    for table in tables:
        if any(pattern in table.lower() for pattern in ['css', 'style', 'theme', 'format', 'layout']):
            css_tables.append(table)
    
    if css_tables:
        print(f"  Found {len(css_tables)} tables with CSS-related names: {', '.join(css_tables)}")
    
    # Check content columns for CSS patterns
    css_patterns = ['{', 'px', 'em', 'rem', '#', 'rgb', '@media', '@font-face', 'url(']
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        for col in columns:
            # Skip non-text columns
            cursor.execute(f"SELECT typeof({col}) FROM {table} LIMIT 1")
            col_type = cursor.fetchone()
            if not col_type or col_type[0].lower() != 'text':
                continue
            
            # Look for CSS-like patterns
            for pattern in css_patterns:
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} LIKE '%{pattern}%'")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"  Found potential CSS in {table}.{col} ({count} rows with '{pattern}')")
                    cursor.execute(f"SELECT {col} FROM {table} WHERE {col} LIKE '%{pattern}%' LIMIT 1")
                    sample = cursor.fetchone()
                    if sample and sample[0]:
                        print(f"  Sample: {sample[0][:150]}...")
                    break
    
    # Look for specific style tables
    style_tables = ['styles', 'css', 'stylesheet', 't_css', 't_style', 't_format']
    for table in style_tables:
        if table in tables:
            print(f"\nFound specific style table: {table}")
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                print(f"  Columns: {', '.join(columns)}")
                for row in rows:
                    print(f"  Row: {row}")


def analyze_database(input_path):
    """Analyze database structure and report details about all tables."""
    print(f"\nAnalyzing database: {input_path}")
    
    try:
        conn = sqlite3.connect(input_path)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Found {len(tables)} tables: {', '.join(tables)}")
    
    # Check database file size
    db_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    print(f"Database file size: {db_size_mb:.2f} MB")
    
    # Analyze each table
    table_stats = {}
    
    for table in tables:
        print(f"\nAnalyzing table: {table}")
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"  Columns: {', '.join(columns)}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        table_stats[table] = row_count
        print(f"  Row count: {row_count:,}")
        
        # Check for key columns
        key_columns = []
        content_columns = []
        id_columns = []
        
        for col in columns:
            if 'midashi' in col.lower() or 'term' in col.lower() or 'word' in col.lower() or 'title' in col.lower():
                key_columns.append(col)
            elif 'content' in col.lower() or 'html' in col.lower() or 'text' in col.lower():
                content_columns.append(col)
            elif 'id' in col.lower() or 'data' in col.lower():
                id_columns.append(col)
        
        if key_columns:
            print(f"  Potential key columns: {', '.join(key_columns)}")
        if content_columns:
            print(f"  Potential content columns: {', '.join(content_columns)}")
        if id_columns:
            print(f"  Potential ID columns: {', '.join(id_columns)}")
        
        # Sample data
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            sample = cursor.fetchone()
            print(f"  Sample row: {sample[:min(5, len(sample))]}...")
            
            # Check if content columns have HTML
            for col in content_columns:
                col_idx = columns.index(col)
                if sample[col_idx] and isinstance(sample[col_idx], str) and '<' in sample[col_idx] and '>' in sample[col_idx]:
                    print(f"  Column '{col}' contains HTML!")
    
    # Show total rows
    total_rows = sum(table_stats.values())
    print(f"\nTotal rows across all tables: {total_rows:,}")
    
    # Sort tables by row count
    sorted_tables = sorted(table_stats.items(), key=lambda x: x[1], reverse=True)
    print("\nTables by row count:")
    for table, count in sorted_tables:
        print(f"  {table}: {count:,}")
    
    # Check for relationships between tables
    print("\nLooking for relationships between tables...")
    for table1 in tables:
        cursor.execute(f"PRAGMA table_info({table1})")
        columns1 = [row[1] for row in cursor.fetchall()]
        
        for col1 in columns1:
            if 'id' in col1.lower() or 'key' in col1.lower():
                for table2 in tables:
                    if table1 != table2:
                        cursor.execute(f"PRAGMA table_info({table2})")
                        columns2 = [row[1] for row in cursor.fetchall()]
                        
                        if col1 in columns2:
                            print(f"  Possible relationship: {table1}.{col1} -> {table2}.{col1}")
    
    check_for_css_patterns(cursor, tables)
    
    conn.close()
    return True

def extract_from_table(cursor, table, args, dictionary):
    """Extract entries from a single table."""
    separator = args.separator
    limit = args.limit
    
    # Get table columns
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Find key and content columns
    key_col = None
    content_col = None
    reading_col = None
    
    # Look for standard column names first
    if 'f_midashi' in columns:
        key_col = 'f_midashi'
    if 'f_contents' in columns:
        content_col = 'f_contents'
    if 'f_midashi_kana' in columns:
        reading_col = 'f_midashi_kana'
    
    # If not found, try to identify by column name patterns
    if not key_col:
        for col in columns:
            if 'midashi' in col.lower() and not 'kana' in col.lower() and not 'prev' in col.lower() and not 'next' in col.lower():
                key_col = col
                break
    
    if not content_col:
        for col in columns:
            if 'content' in col.lower() or 'html' in col.lower() or 'text' in col.lower():
                # Check if it contains HTML
                cursor.execute(f"SELECT {col} FROM {table} WHERE {col} LIKE '%<%>%' LIMIT 1")
                if cursor.fetchone():
                    content_col = col
                    break
    
    if not reading_col and not key_col:
        for col in columns:
            if 'kana' in col.lower() or 'yomi' in col.lower() or 'reading' in col.lower():
                reading_col = col
                break
    
    # Skip table if we can't find both key and content columns
    if not key_col or not content_col:
        print(f"  Skipping table {table}: Cannot identify key and content columns")
        return 0, 0
    
    print(f"  Using key column: {key_col}")
    print(f"  Using content column: {content_col}")
    if reading_col:
        print(f"  Using reading column: {reading_col}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row_count = cursor.fetchone()[0]
    if limit:
        row_count = min(row_count, limit)
    print(f"  Found {row_count:,} entries")
    
    # Build query
    query = f"SELECT {key_col}, {content_col}"
    if reading_col:
        query += f", {reading_col}"
    query += f" FROM {table}"
    if limit:
        query += f" LIMIT {limit}"
    
    # Execute query
    cursor.execute(query)
    
    # Process rows
    processed = 0
    skipped = 0
    start_time = time.time()
    last_report_time = start_time
    
    while True:
        rows = cursor.fetchmany(1000)
        if not rows:
            break
        
        for row in rows:
            term = row[0]
            html = row[1]
            reading = row[2] if reading_col and len(row) > 2 else None
            
            # Skip entries without term or content
            if not term or not html:
                skipped += 1
                continue
            
            # Create key for this entry
            if reading and reading != term:
                key = f"{term}{separator}{reading}"
            else:
                key = term
            
            # Handle duplicate keys
            if key in dictionary:
                counter = 1
                while f"{key}_{counter}" in dictionary:
                    counter += 1
                key = f"{key}_{counter}"
            
            # Add to dictionary
            dictionary[key] = html
            
            # Update progress
            processed += 1
            if processed % 1000 == 0 or processed == 1:
                current_time = time.time()
                if current_time - last_report_time >= 2 or processed <= 5:
                    elapsed = current_time - start_time
                    per_second = processed / elapsed if elapsed > 0 else 0
                    percent = (processed / row_count) * 100
                    
                    print(f"  Progress: {processed:,}/{row_count:,} ({percent:.1f}%) | "
                          f"Speed: {per_second:.1f}/sec")
                    
                    # Show sample entry
                    if processed == 1:
                        print(f"\n  Sample entry from {table}:")
                        print(f"    Key: {key}")
                        print(f"    HTML: {html[:150]}..." if len(html) > 150 else html)
                    
                    last_report_time = current_time
    
    print(f"  Completed {table}: {processed:,} entries extracted, {skipped} skipped")
    return processed, skipped

def extract_dictionary(args):
    """Extract dictionary entries from all suitable tables."""
    input_path = args.input
    output_path = args.output
    
    print(f"\nExtracting dictionary from {input_path}")
    
    try:
        conn = sqlite3.connect(input_path)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Identify content tables (tables that might contain dictionary entries)
    content_tables = []
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Check if table has content and key columns
        has_content = any('content' in col.lower() or 'html' in col.lower() or 'text' in col.lower() for col in columns)
        has_key = any('midashi' in col.lower() or 'term' in col.lower() or 'word' in col.lower() or 'title' in col.lower() for col in columns)
        
        if has_content and has_key:
            content_tables.append(table)
    
    # Also include common table names
    for table in tables:
        if table.startswith('t_contents') or table.startswith('t_dic') or 'dictionary' in table.lower():
            if table not in content_tables:
                content_tables.append(table)
    
    # Fallback - if no content tables found, try all tables
    if not content_tables:
        print("Warning: No obvious content tables found. Trying all tables...")
        content_tables = tables
    
    print(f"Found {len(content_tables)} potential content tables: {', '.join(content_tables)}")
    
    # Process each table
    dictionary = {}
    total_processed = 0
    total_skipped = 0
    start_time = time.time()
    
    for table in content_tables:
        print(f"\nProcessing table: {table}")
        processed, skipped = extract_from_table(cursor, table, args, dictionary)
        total_processed += processed
        total_skipped += skipped
    
    # Check if we have any entries
    if not dictionary:
        print("Error: No entries were extracted from any table.")
        return False
    
    # Write to file
    print(f"\nWriting {len(dictionary):,} entries to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        if args.pretty:
            json.dump(dictionary, f, ensure_ascii=False, indent=2)
        else:
            json.dump(dictionary, f, ensure_ascii=False)
    
    # Final stats
    total_time = time.time() - start_time
    file_size_mb = os.path.getsize(args.output) / (1024 * 1024)
    
    print(f"\nExtraction complete!")
    print(f"  Total entries: {len(dictionary):,}")
    print(f"  Total extracted: {total_processed:,}")
    print(f"  Total skipped: {total_skipped}")
    print(f"  File size: {file_size_mb:.2f} MB")
    print(f"  Time taken: {int(total_time // 60)}m {int(total_time % 60)}s")
    print(f"  Overall speed: {total_processed / total_time:.1f} entries/sec")
    
    conn.close()
    return True

def main():
    print("\n" + "="*60)
    print("NANMED20 Dictionary Extractor")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        args = parse_arguments()
        
        if args.analyze:
            # Just analyze database structure
            analyze_database(args.input)
        else:
            # Extract dictionary
            success = extract_dictionary(args)
            if not success:
                print("\nExtraction failed. Try running with --analyze to understand the database structure.")
                return 1
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())