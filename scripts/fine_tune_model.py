#!/usr/bin/env python3
"""
Fine-tune LLMs for better binary decompilation
"""
import os
import json
import subprocess
from pathlib import Path

class ModelFineTuner:
    def __init__(self, provider="openai"):
        self.provider = provider
        self.training_data_path = Path("training_data")

    def prepare_openai_finetune(self):
        """Prepare and submit fine-tuning job to OpenAI"""

        # Install OpenAI library if not present
        try:
            import openai
        except ImportError:
            subprocess.run(["pip", "install", "openai"])
            import openai

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Upload training file
        try:
            training_file = client.files.create(
                file=open(self.training_data_path / "openai_finetune.jsonl", "rb"),
                purpose="fine-tune"
            )

            print(f"Uploaded training file: {training_file.id}")

            # Create fine-tuning job
            fine_tune_job = client.fine_tuning.jobs.create(
                training_file=training_file.id,
                model="gpt-3.5-turbo",  # Base model
                suffix="binary-decompiler"
            )

            print(f"Fine-tuning job started: {fine_tune_job.id}")
            print(f"Status: {fine_tune_job.status}")

            return fine_tune_job.id

        except Exception as e:
            print(f"Error fine-tuning OpenAI model: {e}")
            return None

    def prepare_local_finetune(self):
        """Setup for local model fine-tuning using transformers"""

        setup_script = '''
# Local fine-tuning setup script
# Install required packages
pip install transformers datasets accelerate

# Create training script
cat > train_decompiler.py << 'EOF'
import json
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer

def load_training_data():
    with open('training_data/examples.json', 'r') as f:
        examples = json.load(f)

    # Format for instruction fine-tuning
    formatted_data = []
    for ex in examples:
        prompt = f"Convert this assembly to C:\n{ex['input']['disassembly']}"
        response = ex['output']['code']

        formatted_data.append({
            'instruction': 'Convert assembly to C code',
            'input': prompt,
            'output': response
        })

    return Dataset.from_list(formatted_data)

def main():
    # Load model and tokenizer
    model_name = "microsoft/DialoGPT-medium"  # Or other suitable base model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    # Add padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load dataset
    dataset = load_training_data()

    # Training arguments
    training_args = TrainingArguments(
        output_dir="./decompiler-model",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=500,
        save_total_limit=2,
        logging_steps=100,
        learning_rate=5e-5,
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )

    # Start training
    trainer.train()

    # Save model
    trainer.save_model("./fine-tuned-decompiler")
    tokenizer.save_pretrained("./fine-tuned-decompiler")

    print("Fine-tuning complete! Model saved to ./fine-tuned-decompiler")

if __name__ == "__main__":
    main()
EOF

# Run training
python train_decompiler.py
'''

        with open("local_finetune_setup.sh", "w") as f:
            f.write(setup_script)

        print("Local fine-tuning setup script created: local_finetune_setup.sh")
        print("Run with: bash local_finetune_setup.sh")

    def generate_larger_dataset(self, num_examples=1000):
        """Generate larger synthetic training dataset"""

        training_examples = []

        # Simple patterns to generate realistic training data
        patterns = [
            {
                "c_code": """int add_numbers(int a, int b) {
    return a + b;
}""",
                "description": "Simple addition function"
            },
            {
                "c_code": """int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}""",
                "description": "Recursive factorial"
            },
            {
                "c_code": """int find_max(int arr[], int size) {
    int max = arr[0];
    for (int i = 1; i < size; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}""",
                "description": "Array traversal with max"
            }
        ]

        # Generate variations
        for i in range(num_examples):
            pattern = patterns[i % len(patterns)]
            training_examples.append({
                "instruction": "Convert assembly to C code",
                "input": f"Assembly code for {pattern['description']}",
                "output": {"code": pattern["c_code"]}
            })

        # Save expanded dataset
        with open(self.training_data_path / "expanded_dataset.json", "w") as f:
            json.dump(training_examples, f, indent=2)

        print(f"Generated {len(training_examples)} training examples")

def main():
    tuner = ModelFineTuner()

    print("=== LLM Fine-Tuning for Binary Decompilation ===")
    print("\n1. Generating training dataset...")
    tuner.generate_larger_dataset(100)

    print("\n2. Preparing OpenAI fine-tuning...")
    job_id = tuner.prepare_openai_finetune()

    print("\n3. Setting up local fine-tuning...")
    tuner.prepare_local_finetune()

    print("\n=== Fine-tuning setup complete! ===")
    print("\nNext steps:")
    print("1. Expand training_data/examples.json with more assembly→C pairs")
    print("2. Run OpenAI fine-tuning job or local training")
    print("3. Update LLM client to use fine-tuned model")
    print("4. Test with known binary samples")

if __name__ == "__main__":
    main()