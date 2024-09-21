# -*- coding: utf-8 -*-
"""Copy of Gemma2b_Final-Sep4.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1X8rDjMUI0SyCyAwyJ-GGw0PdQ1BaNx4Z

#Email subject generation - Instruct Version of Gemma-2b
"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# # Installs Unsloth, Xformers (Flash Attention) and all other packages!
# !pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
# 
# # Check which Torch version for Xformers (2.3 -> 0.0.27)
# from torch import __version__; from packaging.version import Version as V
# xformers = "xformers==0.0.27" if V(__version__) < V("2.4.0") else "xformers"
# 
# !pip install --no-deps {xformers} trl peft accelerate bitsandbytes triton
#

#!pip install triton

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# from unsloth import FastLanguageModel
# import torch
# max_seq_length = 2048 # Auto supports RoPE Scaling internally, via kaiokendev's method.
# dtype = None # None for auto detection. Float16 for Tesla T4.
# load_in_4bit = True # Using 4bit quantization to reduce memory usage.
# 
# fourbit_models = [
#     "unsloth/Meta-Llama-3.1-8B-bnb-4bit",      # Llama-3.1 15 trillion tokens model 2x faster!
#     "unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
#     "unsloth/Meta-Llama-3.1-70B-bnb-4bit",
#     "unsloth/Meta-Llama-3.1-405B-bnb-4bit",    # We also uploaded 4bit for 405b!
#     "unsloth/Mistral-Nemo-Base-2407-bnb-4bit", # New Mistral 12b 2x faster!
#     "unsloth/Mistral-Nemo-Instruct-2407-bnb-4bit",
#     "unsloth/mistral-7b-v0.3-bnb-4bit",        # Mistral v3 2x faster!
#     "unsloth/mistral-7b-instruct-v0.3-bnb-4bit",
#     "unsloth/Phi-3.5-mini-instruct",           # Phi-3.5 2x faster!
#     "unsloth/Phi-3-medium-4k-instruct",
#     "unsloth/gemma-2-9b-bnb-4bit",
#     "unsloth/gemma-2-27b-bnb-4bit",            # Gemma 2x faster!
# ] # More models at https://huggingface.co/unsloth

model, tokenizer = FastLanguageModel.from_pretrained(
              model_name = "unsloth/gemma-2-9b",
              max_seq_length = max_seq_length,
              dtype = dtype,
              load_in_4bit = load_in_4bit,
              # token = "hf_...", # For gated models (when using tokens to access the org specific or gated models like meta-llama/Llama-2-7b-hf)
)

"""##**LoRA adapters**"""

##LoRA adapters (Updates 1 to 10% of all parameters)
## #"unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
model = FastLanguageModel.get_peft_model(
                        model,
                        r = 16, # (or 8, 16, 32, 64, 128)
                        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",],
                        lora_alpha = 16,
                        lora_dropout = 0, # 0 is optimized
                        bias = "none",    # "none" is optimized
                        use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
                        random_state = 3407,
                        use_rslora = False,  # Using Rank stabilized LoRA
                        loftq_config = None, # And LoftQ
                      )

# To delete existing downloded content folder
folder_path = '/content/AESLC/'

# ?

!git clone https://github.com/ryanzhumich/AESLC.git

#Generate JSON file from email dataset
import os
import json
import pandas as pd

# Define the folder containing the text files
folder_path = '/content/AESLC/enron_subject_line/train'

# Initialize lists to store the data
data = []
instruction = 'Please help summarize the provided email body and generate email subject'
# Iterate over each file in the folder
for filename in os.listdir(folder_path):
    #print(filename)
    if filename.endswith(".subject"):
        with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
            content = file.read()
            #print(content)
            # Split the content into body and subject
            if '@subject' in content:
                body_text, subject_text = content.split('@subject')
                data.append({
                    'instruction': instruction,
                    'input': body_text.strip(),
                    'output': subject_text.strip()
                })

# Save the data to a JSON file
json_path = '/content/dataset.json'
print(data) #Before JSon format
with open(json_path, 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

print(data) #After JSon format

print(f"JSON file saved to {json_path}")

"""##Data preparation

"""

email_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""


EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        # EOS_TOKEN, to limit generation to avoid forever generation!
        text = email_prompt.format(instruction, input, output) + EOS_TOKEN
        #print("\n before :", texts)
        #print("\n after :")
        texts.append(text)
    return { "text" : texts, }
pass

# from datasets import load_dataset
# dataset = load_dataset("yahma/alpaca-cleaned", split = "train")
# dataset = dataset.map(formatting_prompts_func, batched = True,)


from datasets import Dataset
import json
# Load your custom dataset
json_path = '/content/dataset.json'
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

#from datasets import load_dataset
#dataset = load_dataset("/content/dataset.json", split = "train")
dataset = Dataset.from_list(data)
dataset = dataset.map(formatting_prompts_func, batched = True,)

"""##Train the model


"""

#Using Huggingface TRL's `SFTTrainer`[TRL SFT docs](https://huggingface.co/docs/trl/sft_trainer).

from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Can make training 5x faster for short sequences.
    args = TrainingArguments(
                  per_device_train_batch_size = 2,
                  #per_device_eval_batch_size=2, ##Opt
                  gradient_accumulation_steps = 4,
                  #evaluation_strategy="steps", ##Opt
                  warmup_steps = 5,
                  #num_train_epochs=3, ##Opt
                  max_steps = 40, ##Tweaked from 60
                  learning_rate = 2e-4,
                  fp16 = not is_bfloat16_supported(),
                  bf16 = is_bfloat16_supported(),
                  logging_steps = 1,
                  optim = "adamw_8bit",
                  weight_decay = 0.01,
                  lr_scheduler_type = "linear",
                  seed =  3407,
                  output_dir = "outputs",
              ),
)

#Try & set `num_train_epochs=1` for a full run, and turn off `max_steps=None`. Support TRL's `DPOTrainer`!

"""###Current memory stats"""

print("Current Memory Stats:")
gpu_stats = torch.cuda.get_device_properties(0)
start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
# print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
# print(f"{start_gpu_memory} GB of memory reserved.")
print(f"GPU = {gpu_stats.name}")
print(f"Max memory = {max_memory} GB")
print(f"Memory reserved = {start_gpu_memory} GB")
print("-----------------------------------------------------------------")

trainer_stats = trainer.train()

#@title Show final memory and time stats
used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
used_memory_for_lora = round(used_memory - start_gpu_memory, 3)
used_percentage = round(used_memory /max_memory*100, 3)
lora_percentage = round(used_memory_for_lora/max_memory*100, 3)
print("Training Memory Stats:")
print(f"{round(trainer_stats.metrics['train_runtime']/60, 2)} minutes used for training.")
print(f"{trainer_stats.metrics['train_runtime']} seconds used for training.")
print(f"Peak reserved memory = {used_memory} GB.")
print(f"Peak reserved memory for training = {used_memory_for_lora} GB.")
print(f"Peak reserved memory % of max memory = {used_percentage} %.")
print(f"Peak reserved memory for training % of max memory = {lora_percentage} %.")
print("-----------------------------------------------------------------------------------------")

"""<a name="Inference"></a>
### Inference
"""

#Run the model! Change the instruction & input, and leave output blank!
#email_prompt = Copied from above
FastLanguageModel.for_inference(model) #Enable native 2x faster inference
inputs = tokenizer(
[
    email_prompt.format(
        "Please help summarize the provided email body and generate email subject", #Instruction
        "Kevin Presto is requesting that you attend a meeting regarding Organizing an Action Plan for the Start-up of Netco.\nThe meeting will be held in ECS 06716 at 9:30 am, Wednesday, January 2, 2002.\nFor Tim and Chris, could you please call 713-584-2067.\nThis is the telephone number in the conference room.\nIf you should have any questions, please call T Jae Black at 3-5800.\nThanks", #input
        "", #output - leave this blank for generation!
    )
  ], return_tensors = "pt").to("cuda")

outputs = model.generate(**inputs, max_new_tokens = 64, use_cache = True)
tokenizer.batch_decode(outputs)

##Substring to fetch only response

"""###TextStreamer for continuous inference"""

#Use `TextStreamer` for continuous inference - to view generation token by token, instead of waiting for the entire duration.
#email_prompt = Copied from above
FastLanguageModel.for_inference(model) # Enable native 2x faster inference
inputs = tokenizer(
[
    email_prompt.format(
        "Please help summarize the provided email body and generate email subject", # instruction
         #"Kevin Presto is requesting that you attend a meeting regarding Organizing an Action Plan for the Start-up of Netco.\nThe meeting will be held in ECS 06716 at 9:30 am, Wednesday, January 2, 2002.\nFor Tim and Chris, could you please call 713-584-2067.\nThis is the telephone number in the conference room.\nIf you should have any questions, please call T Jae Black at 3-5800.\nThanks", #input
         "The following reports have been waiting for your approval for more than 4 days.Please review.Owner: James W Reitmeyer Report Name: JReitmeyer 10/24/01 Days In Mgr.Queue: 5", # input

        #"Phillip,   Could you please do me a favor?I would like  to read your current title policy to see what it says about easements.You  should have received a copy during your closing.I don't know how many  pages it will be but let me know how you want to handle getting a copy  made.I'll be happy to make the copy, or whatever makes it easy for  you.Thanks,", # input
        "", # output - leave this blank for generation!
    )
], return_tensors = "pt").to("cuda")

from transformers import TextStreamer
text_streamer = TextStreamer(tokenizer)
_ = model.generate(**inputs, streamer = text_streamer, max_new_tokens = 128)

"""<a name="Save"></a>
### Saving, loading finetuned models


"""

#To save LoRA adapters (not full model)
#To save the final model as LoRA adapters, use `save_pretrained` to save locally
#(otherwise Huggingface's `push_to_hub` to save online).

model.save_pretrained("EmailSubGen_Gemma2b_lora_model") # Local saving
tokenizer.save_pretrained("EmailSubGen_Gemma2b_lora_model")
# model.push_to_hub("your_name/lora_model", token = "...") # Online saving
# tokenizer.push_to_hub("your_name/lora_model", token = "...") # Online saving

##!unzip EmailSubGen_lora_model.zip

"""Lload the LoRA adapters we just saved for inference"""

#Set `False' to `True' to load the LoRA adapters
if True:
    from unsloth import FastLanguageModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "EmailSubGen_Gemma2b_lora_model", # YOUR MODEL YOU USED FOR TRAINING
        max_seq_length = max_seq_length,
        dtype = dtype,
        load_in_4bit = load_in_4bit,
        #load_in_8bit_fp32_cpu_offload=True, # Add this line to enable CPU offloading
        device_map={"":0} # Add this line to specify GPU 0 for model placement
    )
    FastLanguageModel.for_inference(model) # Enable native 2x faster inference

inputs = tokenizer(
[
    email_prompt.format(
        "Please help summarize the provided email body and generate email subject", # instruction
        "The following reports have been waiting for your approval for more than 4 days.Please review.Owner: James W Reitmeyer Report Name: JReitmeyer 10/24/01 Days In Mgr.Queue: 5", # input
        "", # output - leave this blank for generation!
    ),
], return_tensors = "pt").to("cuda")

outputs = model.generate(**inputs, max_new_tokens = 64, use_cache = True)
print("\n")
tokenizer.batch_decode(outputs)

"""##Save model - locally"""

# prompt: zip folder /content/EmailSubGen_Gemma2_lora_model and upload to google drive

!zip -r /content/EmailSubGen_Gemma2_lora_model.zip /content/EmailSubGen_Gemma2_lora_model

from google.colab import drive
drive.mount('/content/drive')
!cp /content/EmailSubGen_Gemma2_lora_model.zip /content/drive/MyDrive

"""**Transfer content from text to Jason**"""

import os
import json
import pandas as pd

# Define the folder containing the text files
folder_path = '/content/AESLC/enron_subject_line/test'

# Initialize lists to store the data
data = []
instruction = 'Please help summarize the provided email body and generate email subject'
# Iterate over each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".subject"):
        with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
            content = file.read()
            # Split the content into body and subject
            if '@subject' in content:
                body_text, subject_text = content.split('@subject')

                lines = subject_text.strip().splitlines()  # Split by lines and remove leading/trailing whitespace
                output = []
                for line in lines:
                    if line.strip():
                        if line.startswith("@"):
                            annotation = line.split()[1:]  # Extract annotation text after "@" and split by space
                            if len(annotation):
                                output.append("".join(annotation))  # Join words in annotation back together
                        else:
                            output.append(line.strip())  # Add subject or remaining text after removing whitespace
                data.append({
                    'instruction': instruction,
                    'input': body_text.strip(),
                    'output': output
                })

# Save the data to a JSON file
json_path = '/content/AESLC/enron_subject_line/test/testdataset.json'
with open(json_path, 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

print(f"JSON file saved to {json_path}")

email_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""


EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        # Must add EOS_TOKEN, otherwise your generation will go on forever!
        text = email_prompt.format(instruction, input, output) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }
pass

from datasets import Dataset
import json
# Load your custom dataset
json_path = '/content/AESLC/enron_subject_line/test/testdataset.json'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

testdataset = Dataset.from_list(data[:100])
testdataset = dataset.map(formatting_prompts_func, batched = True,)

"""#Rouge"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# !pip install rouge
# !pip install evaluate
# !pip install rouge_score

from transformers import pipeline
from evaluate import load

# Load - ROUGE metric
rouge = load("rouge")

# Create a text generation pipeline
generator = pipeline(task="text-generation", model=model, tokenizer=tokenizer)

# Generate predictions on the test dataset
# Access the input column of the dataset using the column name
predictions = generator(
    testdataset[:800]["input"],
    max_new_tokens=10, #10 for Gemma, 100 for llama
    num_beams=1,
)

# Extract the generated text from the pipeline output
predictions = [pred[0]['generated_text'] for pred in predictions]


# Compute ROUGE metrics
results = rouge.compute(predictions=predictions, references=testdataset[:800]["output"])

# for resultItem in results:
# print(resultItem)

print(results)

##Observations from AUG 8th-9th:
# <4min   max_steps = 50    testdataset[:100]["input"],max_new_tokens=20,  ----  {'rouge1': 0.04703338794882978, 'rouge2': 0.018094740811992135, 'rougeL': 0.04291153191710728, 'rougeLsum': 0.044421997423522985}
# 4mins   max_steps = 50    testdataset[:300]["input"],max_new_tokens=20,  ----  {'rouge1': 0.04763686796739476, 'rouge2': 0.018590431359526753, 'rougeL': 0.04346346295047031, 'rougeLsum': 0.04518140308108524}
# 5mins   max_steps = 50    testdataset[:400]["input"],max_new_tokens=20,  ----  {'rouge1': 0.04841968575892602, 'rouge2': 0.018794301094831288, 'rougeL': 0.04393371452433795, 'rougeLsum': 0.04536474990806128}
# 12mins   max_steps = 50    testdataset[:800]["input"],max_new_tokens=20,  ----  {'rouge1': 0.04890688956561573, 'rouge2': 0.018216384865342265, 'rougeL': 0.0442624056719164, 'rougeLsum': 0.04646280874733754}
# 10mins   max_steps = 40, seed=5000    testdataset[:800]["input"],max_new_tokens=20,  ---- {'rouge1': 0.05063502156641153, 'rouge2': 0.018875734537863367, 'rougeL': 0.04545903906916432, 'rougeLsum': 0.04815762881014813}
# 8mins   max_steps = 40, seed=5000    testdataset[:800]["input"],max_new_tokens=15,  ---- {'rouge1': 0.052136084070747046, 'rouge2': 0.019510195273507815, 'rougeL': 0.04683298782296529, 'rougeLsum': 0.04945309030336453}
# 14mins   max_steps = 40, seed=5000   testdataset[:1200]["input"],max_new_tokens=20,  ---- {'rouge1': 0.05058661057227369, 'rouge2': 0.019035910262427347, 'rougeL': 0.04597646530256609, 'rougeLsum': 0.04820730672046365}
# 7mins   max_steps = 40, seed=5000    testdataset[:1200]["input"],max_new_tokens=15,  ---- {'rouge1': 0.05206475367626734, 'rouge2': 0.019660981842852962, 'rougeL': 0.047334418031740016, 'rougeLsum': 0.04955124524476833}
# 7mins   max_steps = 40, seed=5000    testdataset[:1200]["input"],max_new_tokens=15,  ---- {'rouge1': 0.05378414875142114,  'rouge2': 0.020305912892399518, 'rougeL': 0.04887783094017359,  'rougeLsum': 0.051091497309520784}
# 14mins   max_steps = 40, seed=5000   testdataset[:2000]["input"],max_new_tokens=10,  ---- {'rouge1': 0.052309203096362944, 'rouge2': 0.019196742044162142, 'rougeL': 0.04750068460138787, 'rougeLsum': 0.04933446927139551}
# 12mins   max_steps = 40, seed=5000   testdataset[:2000]["input"],max_new_tokens=8,  ---- {'rouge1': 0.05432970692439458, 'rouge2': 0.01982842310030821, 'rougeL': 0.0486903691067596, 'rougeLsum': 0.0510405649164995}
# 14mins   max_steps = 40, seed=5000   testdataset[:2000]["input"],max_new_tokens=100, ----  {'rouge1': 0.05010987187520588, 'rouge2': 0.01837820157743939, 'rougeL': 0.04565723455877756, 'rougeLsum': 0.04739943293133862}
# 12mins, max_steps = 50  seed=3511  testdataset[:1000]["input"],max_new_tokens=10,  ----   {'rouge1': 0.05010987187520588, 'rouge2': 0.01837820157743939, 'rougeL': 0.04565723455877756, 'rougeLsum': 0.04739943293133862}
# 6mins   max_steps = 40, seed=5000   testdataset[:1000]["input"],max_new_tokens=8, ----  {'rouge1': 0.05295198263076574, 'rouge2': 0.019339196256452373, 'rougeL': 0.04794131858578204, 'rougeLsum': 0.050042551446080094}
# 6mins   max_steps = 40, seed=5000  random_state = 1100 testdataset[:1000]["input"],max_new_tokens=8,
## --- {'rouge1': 0.052935694565499666, 'rouge2': 0.019348959418414594, 'rougeL': 0.047953921679959516, 'rougeLsum': 0.050015091457237065}

 # 12mins  max_steps = 40, seed=5000 random_state = 5000   testdataset[:2000]["input"],max_new_tokens=8, ----
 ## ---  {'rouge1': 0.05432970692439458, 'rouge2': 0.01982842310030821, 'rougeL': 0.0486903691067596, 'rougeLsum': 0.0510405649164995}

if False:
    # Set to False to use Unsloth
    from peft import AutoPeftModelForCausalLM
    from transformers import AutoTokenizer
    model = AutoPeftModelForCausalLM.from_pretrained(
        "lora_model", # MODEL USED FOR TRAINING
        load_in_4bit = load_in_4bit,
    )
    tokenizer = AutoTokenizer.from_pretrained("lora_model")

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# # Save to q4_k_m GGUF
# # `q4_k_m` - Recommended. Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q4_K.
# model.save_pretrained_gguf("model", tokenizer, quantization_method = "q4_k_m")

# prompt: copy the unsloth.Q4_K_M.gguf to google drive

from google.colab import drive
drive.mount('/content/drive')

!cp /content/model/unsloth.Q4_K_M.gguf /content/drive/MyDrive