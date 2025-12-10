import os

def get_next_chunk_number(base_dir, run_name):
    chunk_dirs = [d for d in os.listdir(base_dir) if d.startswith(f"{run_name}_chunk_")]
                  
    # Empty dir: start from scratch
    if not chunk_dirs:
        return 1

    # Check for incomplete chunks (missing caseInfo file)
    chunk_numbers = []
    for d in chunk_dirs:
        chunk_num = int(d.split("_chunk_")[1])
        chunk_numbers.append(chunk_num)
        
        # Check if this chunk has a caseInfo file
        chunk_path = os.path.join(base_dir, d)
        caseinfo_files = [f for f in os.listdir(chunk_path) if f.endswith('.caseInfo')]
        
        if not caseinfo_files:
            # Found an incomplete chunk, return its number
            return chunk_num
    
    # All chunks are complete, return the next number
    return max(chunk_numbers) + 1