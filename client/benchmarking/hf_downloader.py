import argparse
from huggingface_hub import hf_hub_download

def download_model(repo_id, filename, output_dir):
    try:
        # Download the file
        file_path = hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=output_dir)
        print(f'Model downloaded to: {file_path}')
    except Exception as e:
        print(f'Error downloading model: {e}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download GGUF model files from Hugging Face.")
    parser.add_argument('--repo_id', type=str, required=True, help="Repository ID (e.g., 'TheBloke/CodeLlama-7B-GGUF')")
    parser.add_argument('--filename', type=str, required=True, help="Filename of the model (e.g., 'codellama-7b.q4_K_M.gguf')")
    parser.add_argument('--output_dir', type=str, default='.', help="Directory to save the downloaded model")

    args = parser.parse_args()
    download_model(args.repo_id, args.filename, args.output_dir)