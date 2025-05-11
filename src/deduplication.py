#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

class DeduplicationManager:
    """
    Manages deduplication of snapshot data to minimize storage usage.
    Implements both file-level and block-level deduplication.
    """
    
    def __init__(self, config_path: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self._initialize_dedup_storage()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _initialize_dedup_storage(self) -> None:
        """Initialize deduplication storage directory."""
        dedup_dir = Path(self.config['storage']['deduplication_directory'])
        dedup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create blocks directory for block-level deduplication
        blocks_dir = dedup_dir / "blocks"
        blocks_dir.mkdir(exist_ok=True)
        
        # Create index file if it doesn't exist
        index_file = dedup_dir / "dedup_index.json"
        if not index_file.exists():
            default_index = {
                "file_hashes": {},
                "block_hashes": {},
                "stats": {
                    "total_files": 0,
                    "deduplicated_files": 0,
                    "total_blocks": 0,
                    "deduplicated_blocks": 0,
                    "space_saved": 0
                }
            }
            with open(index_file, 'w') as f:
                json.dump(default_index, f, indent=2)
    
    def _load_dedup_index(self) -> Dict:
        """Load deduplication index."""
        dedup_dir = Path(self.config['storage']['deduplication_directory'])
        index_file = dedup_dir / "dedup_index.json"
        
        with open(index_file, 'r') as f:
            return json.load(f)
    
    def _save_dedup_index(self, index: Dict) -> None:
        """Save deduplication index."""
        dedup_dir = Path(self.config['storage']['deduplication_directory'])
        index_file = dedup_dir / "dedup_index.json"
        
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def deduplicate_snapshot(self, snapshot_path: Path) -> Dict:
        """
        Deduplicate files in a snapshot.
        
        Args:
            snapshot_path: Path to the snapshot directory
            
        Returns:
            Dictionary with deduplication statistics
        """
        if not snapshot_path.exists() or not snapshot_path.is_dir():
            self.logger.error(f"Snapshot directory not found: {snapshot_path}")
            return {"error": "Snapshot directory not found"}
        
        # Load deduplication configuration
        dedup_config = self.config.get("storage", {}).get("deduplication", {})
        method = dedup_config.get("method", "file")  # "file" or "block"
        block_size = dedup_config.get("block_size", 4096)  # Block size in bytes
        
        # Initialize statistics
        stats = {
            "snapshot": str(snapshot_path),
            "method": method,
            "files_processed": 0,
            "files_deduplicated": 0,
            "blocks_processed": 0,
            "blocks_deduplicated": 0,
            "space_saved": 0
        }
        
        # Process based on method
        if method == "file":
            self._deduplicate_files(snapshot_path, stats)
        elif method == "block":
            self._deduplicate_blocks(snapshot_path, stats, block_size)
        else:
            self.logger.error(f"Unknown deduplication method: {method}")
            return {"error": f"Unknown deduplication method: {method}"}
        
        # Create deduplication metadata for the snapshot
        metadata_file = snapshot_path / ".deduplication_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                "timestamp": str(datetime.datetime.now()),
                "method": method,
                "stats": stats
            }, f, indent=2)
        
        self.logger.info(f"Deduplication completed for {snapshot_path}: "
                        f"saved {stats['space_saved']} bytes")
        
        return stats
    
    def _deduplicate_files(self, snapshot_path: Path, stats: Dict) -> None:
        """
        Perform file-level deduplication.
        
        Args:
            snapshot_path: Path to the snapshot directory
            stats: Dictionary to update with statistics
        """
        # Load the deduplication index
        index = self._load_dedup_index()
        file_hashes = index["file_hashes"]
        dedup_dir = Path(self.config['storage']['deduplication_directory'])
        
        # Process all files in the snapshot
        for file_path in snapshot_path.rglob("*"):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue
            
            stats["files_processed"] += 1
            
            try:
                # Calculate file hash
                file_hash = self._calculate_file_hash(file_path)
                
                # Check if this file already exists in the index
                if file_hash in file_hashes:
                    # File exists, create a hard link or symbolic link
                    original_path = Path(file_hashes[file_hash]["path"])
                    
                    if original_path.exists():
                        # Get file size before removing
                        file_size = file_path.stat().st_size
                        
                        # Remove the duplicate file
                        file_path.unlink()
                        
                        # Create a hard link if possible, otherwise symbolic link
                        try:
                            os.link(original_path, file_path)
                            link_type = "hard"
                        except OSError:
                            os.symlink(original_path, file_path)
                            link_type = "symbolic"
                        
                        # Update statistics
                        stats["files_deduplicated"] += 1
                        stats["space_saved"] += file_size
                        
                        # Update reference count in index
                        file_hashes[file_hash]["references"] += 1
                        file_hashes[file_hash]["snapshots"].append(str(snapshot_path))
                        
                        self.logger.debug(f"Deduplicated file: {file_path} "
                                         f"({link_type} link to {original_path})")
                    else:
                        # Original file no longer exists, update the index with this file
                        file_hashes[file_hash] = {
                            "path": str(file_path),
                            "size": file_path.stat().st_size,
                            "references": 1,
                            "snapshots": [str(snapshot_path)]
                        }
                else:
                    # New file, add to index
                    file_hashes[file_hash] = {
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "references": 1,
                        "snapshots": [str(snapshot_path)]
                    }
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
        
        # Update the index
        index["file_hashes"] = file_hashes
        index["stats"]["total_files"] = len(file_hashes)
        index["stats"]["deduplicated_files"] = sum(1 for h in file_hashes.values() if h["references"] > 1)
        index["stats"]["space_saved"] += stats["space_saved"]
        
        self._save_dedup_index(index)
    
    def _deduplicate_blocks(self, snapshot_path: Path, stats: Dict, block_size: int) -> None:
        """
        Perform block-level deduplication.
        
        Args:
            snapshot_path: Path to the snapshot directory
            stats: Dictionary to update with statistics
            block_size: Size of blocks in bytes
        """
        # Load the deduplication index
        index = self._load_dedup_index()
        block_hashes = index["block_hashes"]
        dedup_dir = Path(self.config['storage']['deduplication_directory'])
        blocks_dir = dedup_dir / "blocks"
        
        # Process all files in the snapshot
        for file_path in snapshot_path.rglob("*"):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue
            
            stats["files_processed"] += 1
            
            try:
                # Create a blocks directory for this file if it doesn't exist
                rel_path = file_path.relative_to(snapshot_path)
                file_blocks_dir = blocks_dir / rel_path.parent
                file_blocks_dir.mkdir(parents=True, exist_ok=True)
                
                # Create a block map file
                block_map_file = file_blocks_dir / f"{rel_path.name}.blockmap"
                block_map = []
                
                # Process the file in blocks
                with open(file_path, 'rb') as f:
                    file_size = file_path.stat().st_size
                    block_count = (file_size + block_size - 1) // block_size  # Ceiling division
                    
                    for block_index in range(block_count):
                        f.seek(block_index * block_size)
                        block_data = f.read(block_size)
                        
                        stats["blocks_processed"] += 1
                        
                        # Calculate block hash
                        block_hash = hashlib.sha256(block_data).hexdigest()
                        
                        # Check if this block already exists
                        if block_hash in block_hashes:
                            # Block exists, reference it
                            block_map.append({
                                "index": block_index,
                                "hash": block_hash,
                                "size": len(block_data)
                            })
                            
                            # Update reference count
                            block_hashes[block_hash]["references"] += 1
                            
                            stats["blocks_deduplicated"] += 1
                            stats["space_saved"] += len(block_data)
                        else:
                            # New block, store it
                            block_file = blocks_dir / f"{block_hash[:2]}" / f"{block_hash[2:4]}" / block_hash
                            block_file.parent.mkdir(parents=True, exist_ok=True)
                            
                            with open(block_file, 'wb') as bf:
                                bf.write(block_data)
                            
                            # Add to index
                            block_hashes[block_hash] = {
                                "path": str(block_file),
                                "size": len(block_data),
                                "references": 1
                            }
                            
                            # Add to block map
                            block_map.append({
                                "index": block_index,
                                "hash": block_hash,
                                "size": len(block_data)
                            })
                
                # Save the block map
                with open(block_map_file, 'w') as f:
                    json.dump({
                        "file": str(rel_path),
                        "original_size": file_size,
                        "block_size": block_size,
                        "blocks": block_map
                    }, f, indent=2)
                
                # Replace the original file with a reference file
                file_path.unlink()
                with open(file_path, 'w') as f:
                    f.write(f"DEDUP_BLOCKMAP:{str(block_map_file)}")
                
            except Exception as e:
                self.logger.error(f"Error processing file {file_path} for block deduplication: {e}")
        
        # Update the index
        index["block_hashes"] = block_hashes
        index["stats"]["total_blocks"] = len(block_hashes)
        index["stats"]["deduplicated_blocks"] = sum(1 for h in block_hashes.values() if h["references"] > 1)
        index["stats"]["space_saved"] += stats["space_saved"]
        
        self._save_dedup_index(index)
    
    def restore_deduplicated_file(self, file_path: Path) -> bool:
        """
        Restore a deduplicated file to its original content.
        
        Args:
            file_path: Path to the deduplicated file
            
        Returns:
            True if restoration was successful, False otherwise
        """
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False
        
        try:
            # Check if this is a block-mapped file
            with open(file_path, 'r') as f:
                content = f.read()
            
            if content.startswith("DEDUP_BLOCKMAP:"):
                # This is a block-mapped file
                block_map_file = Path(content[len("DEDUP_BLOCKMAP:"):])
                
                if not block_map_file.exists():
                    self.logger.error(f"Block map file not found: {block_map_file}")
                    return False
                
                # Load the block map
                with open(block_map_file, 'r') as f:
                    block_map = json.load(f)
                
                # Create a temporary file for restoration
                temp_file = file_path.with_suffix(".restored")
                
                # Reconstruct the file from blocks
                with open(temp_file, 'wb') as f:
                    for block in block_map["blocks"]:
                        block_hash = block["hash"]
                        block_file = Path(self.config['storage']['deduplication_directory']) / "blocks" / \
                                    f"{block_hash[:2]}" / f"{block_hash[2:4]}" / block_hash
                        
                        if not block_file.exists():
                            self.logger.error(f"Block file not found: {block_file}")
                            temp_file.unlink()
                            return False
                        
                        # Read the block and write to the output file
                        with open(block_file, 'rb') as bf:
                            block_data = bf.read()
                        
                        f.write(block_data)
                
                # Replace the original file with the restored file
                file_path.unlink()
                temp_file.rename(file_path)
                
                self.logger.info(f"Restored block-deduplicated file: {file_path}")
                return True
            else:
                # This might be a hard link or symbolic link, but we don't need to do anything
                # as the file content is already accessible
                return True
        except Exception as e:
            self.logger.error(f"Error restoring deduplicated file {file_path}: {e}")
            return False
    
    def restore_deduplicated_snapshot(self, snapshot_path: Path) -> Dict:
        """
        Restore all deduplicated files in a snapshot.
        
        Args:
            snapshot_path: Path to the snapshot directory
            
        Returns:
            Dictionary with restoration statistics
        """
        if not snapshot_path.exists() or not snapshot_path.is_dir():
            self.logger.error(f"Snapshot directory not found: {snapshot_path}")
            return {"error": "Snapshot directory not found"}
        
        stats = {
            "snapshot": str(snapshot_path),
            "files_processed": 0,
            "files_restored": 0,
            "failed_restorations": 0
        }
        
        # Check if this snapshot was deduplicated
        metadata_file = snapshot_path / ".deduplication_metadata.json"
        if not metadata_file.exists():
            self.logger.info(f"No deduplication metadata found for {snapshot_path}")
            return stats
        
        # Process all files in the snapshot
        for file_path in snapshot_path.rglob("*"):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue
            
            stats["files_processed"] += 1
            
            try:
                if self.restore_deduplicated_file(file_path):
                    stats["files_restored"] += 1
                else:
                    stats["failed_restorations"] += 1
            except Exception as e:
                self.logger.error(f"Error restoring file {file_path}: {e}")
                stats["failed_restorations"] += 1
        
        # Remove the deduplication metadata
        metadata_file.unlink()
        
        self.logger.info(f"Restored {stats['files_restored']} deduplicated files in {snapshot_path} "
                        f"({stats['failed_restorations']} failures)")
        
        return stats
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate a hash for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hash string
        """
        hash_obj = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):  # Read in 64k chunks
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def get_deduplication_stats(self) -> Dict:
        """
        Get overall deduplication statistics.
        
        Returns:
            Dictionary with statistics
        """
        index = self._load_dedup_index()
        return index["stats"]
    
    def cleanup_orphaned_blocks(self) -> int:
        """
        Clean up orphaned blocks that are no longer referenced.
        
        Returns:
            Number of blocks removed
        """
        index = self._load_dedup_index()
        block_hashes = index["block_hashes"]
        blocks_dir = Path(self.config['storage']['deduplication_directory']) / "blocks"
        
        # Find blocks with no references
        orphaned_blocks = [h for h, data in block_hashes.items() if data["references"] == 0]
        
        # Remove orphaned blocks
        removed_count = 0
        for block_hash in orphaned_blocks:
            block_file = Path(block_hashes[block_hash]["path"])
            
            if block_file.exists():
                block_file.unlink()
                removed_count += 1
                del block_hashes[block_hash]
        
        # Update the index
        index["block_hashes"] = block_hashes
        index["stats"]["total_blocks"] = len(block_hashes)
        self._save_dedup_index(index)
        
        self.logger.info(f"Removed {removed_count} orphaned blocks")
        
        return removed_count