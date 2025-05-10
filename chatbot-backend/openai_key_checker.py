#!/usr/bin/env python3
"""
OpenAI API Key Checker
This script verifies if an OpenAI API key is valid by making a simple test request.
"""
import os
import sys
import requests
import argparse

def check_openai_key(api_key):
    """
    Check if the OpenAI API key is valid by making a simple request to list models.
    
    Args:
        api_key (str): The OpenAI API key to check
        
    Returns:
        bool: True if the key is valid, False otherwise
    """
    url = "https://api.openai.com/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("✅ API key is valid!")
            print(f"Status code: {response.status_code}")
            
            # Optional: Display available models
            models = response.json().get("data", [])
            if models:
                print("\nAvailable models:")
                for model in models[:5]:  # Show first 5 models
                    print(f"- {model['id']}")
                if len(models) > 5:
                    print(f"... and {len(models) - 5} more")
            
            return True
        else:
            print("❌ API key is invalid or has issues!")
            print(f"Status code: {response.status_code}")
            print(f"Error message: {response.text}")
            return False
    except Exception as e:
        print("❌ Error occurred while checking the API key!")
        print(f"Error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Check if an OpenAI API key is valid")
    parser.add_argument("--key", help="OpenAI API key to check")
    args = parser.parse_args()
    
    # Get API key from argument or environment variable or prompt
    api_key = args.key or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        api_key = input("Enter your OpenAI API key to check: ").strip()
    
    if not api_key:
        print("No API key provided. Exiting.")
        sys.exit(1)
    
    # Check the API key
    is_valid = check_openai_key(api_key)
    
    # Exit with appropriate status code
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()