# Email Subject Generation (Group 18)

## Description
Generate a succinct subject line from the body of an email.
Email Subject Line Generation task involves identifying the most important sentences in an email and abstracting their message into just a few words. The project provides an opportunity to work with generative models in NLP, specifically using GPT-2 variants, and to explore different metrics for evaluating text generation. \
**Project Proposal**: [Group 18 - Capstone Project proposal - Google Docs.pdf](https://github.com/anukvma/group18_email_subject_generation/blob/main/Group%2018%20-%20Capstone%20Project%20proposal%20-%20Google%20Docs.pdf)

## DataSet
Dataset used is from the below repository for fine tuning the models
The Annotated Enron Subject Line Corpus: https://github.com/ryanzhumich/AESLC

## Models
The following models are fine tuned 
| LLM     	| Framework             | Model Type        | Training Steps       	| Evaluation Method    	| 
|---------	|---------------------	|-------------------|---------------------	|----------------------	|
| Mistral 	| unsloth             	| 4 bit quantized 	| 60 	                  | ROUGE Score         	|
| Llama3  	| unsloth             	| 4 bit quantized 	| 60  	                | ROUGE Score           |
| T5      	| Transformer           | Base model       	| 200                  	| ROUGE Score          	|
| Bart    	| Transformer           | Base model       	| 200                  	| ROUGE Score          	|

## Training Details

### Mistral
**Code File**: [Group18EmailDataSetTrainingMistral.ipynb](https://github.com/anukvma/group18_email_subject_generation/blob/main/Group18EmailDataSetTrainingMistral.ipynb) \
Model: unsloth/mistral-7b-v0.3-bnb-4bit 
```
FastLanguageModel.get_peft_model(
    model,
    r = 16, # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, # Supports any, but = 0 is optimized
    bias = "none",    # Supports any, but = "none" is optimized
    # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
    use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
    random_state = 3407,
    use_rslora = False,  # We support rank stabilized LoRA
    loftq_config = None, # And LoftQ
)
```
Training Framework: Huggingface trl [SFTrainer](https://huggingface.co/docs/trl/v0.9.6/en/sft_trainer#trl.SFTTrainer) \
Training Arguments:
```
TrainingArguments(
    per_device_train_batch_size = 2,
    per_device_eval_batch_size=2,
    gradient_accumulation_steps = 4,
    evaluation_strategy="steps",
    warmup_steps = 5,
    num_train_epochs=3,
    max_steps = 60, # Set num_train_epochs = 1 for full training runs
    learning_rate = 2e-4,
    fp16 = not is_bfloat16_supported(),
    bf16 = is_bfloat16_supported(),
    logging_steps = 1,
    optim = "adamw_8bit",
    weight_decay = 0.01,
    lr_scheduler_type = "linear",
    seed = 3407,
    output_dir = "outputs",
#      report_to="wandb",  # enable logging to W&B
    logging_strategy = 'steps',
   # save_total_limit=2,
)
```

### LLAMA3
**Code File**: [Group18FineTuneLlama3EmailSubjectFinal.ipynb.ipynb](https://github.com/anukvma/group18_email_subject_generation/blob/main/Group18FineTuneLlama3EmailSubjectFinal.ipynb.ipynb) \
Model: unsloth/llama-3-8b-bnb-4bit
```
FastLanguageModel.get_peft_model(
    model,
    r = 16, # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, # Supports any, but = 0 is optimized
    bias = "none",    # Supports any, but = "none" is optimized
    # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
    use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
    random_state = 3407,
    use_rslora = False,  # We support rank stabilized LoRA
    loftq_config = None, # And LoftQ
)
```
Training Framework: Huggingface trl [SFTrainer](https://huggingface.co/docs/trl/v0.9.6/en/sft_trainer#trl.SFTTrainer) \
Training Arguments:
```
TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60,
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    )
```
### T5
**Code File**: [Group18FineTuningT5EmailSubject.ipynb](https://github.com/anukvma/group18_email_subject_generation/blob/main/Group18FineTuningT5EmailSubject.ipynb) \
Model: t5-base \
Training Framework: Transformer Seq2SeqTrainer \
Training Arguments: 
```
Seq2SeqTrainingArguments(
    model_dir,
    evaluation_strategy="steps",
    eval_steps=200,
    logging_strategy="steps",
    logging_steps=100,
    save_strategy="steps",
    save_steps=200,
    learning_rate=4e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=2,
    predict_with_generate=True,
    fp16=True,
    load_best_model_at_end=True,
    metric_for_best_model="rouge1",
    report_to="tensorboard"
)
```
### Bart
**Code File**: [Group18FineTuneBartEmailSubjectFinal.ipynb](https://github.com/anukvma/group18_email_subject_generation/blob/main/Group18FineTuneBartEmailSubjectFinal.ipynb) \
Model: facebook/bart-large-xsum \
Training Framework: Transformer Seq2SeqTrainer \
Training Arguments: 
```
Seq2SeqTrainingArguments(
    model_dir,
    evaluation_strategy="steps",
    eval_steps=200,
    logging_strategy="steps",
    logging_steps=100,
    save_strategy="steps",
    save_steps=200,
    learning_rate=4e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=2,
    predict_with_generate=True,
    fp16=True,
    load_best_model_at_end=True,
    metric_for_best_model="rouge1",
    report_to="tensorboard"
)
```
## Inference Results

### Email Body:
﻿Please help summarize the provided email body and generate email subject Kevin Presto is requesting that you attend a meeting regarding Organizing an Action Plan for the Start-up of Netco.\nThe meeting will be held in ECS 06716 at 9:30 am, Wednesday, January 2, 2002.\nFor Tim and Chris, could you please call 713-584-2067.\nThis is the telephone number in the conference room.\nIf you should have any questions, please call T Jae Black at 3-5800.\nThanks
 
### Reference Output:
meeting regarding the netco start up action plan

### Llama3 Model Output:
﻿Netco Action Plan Meeting

### Mistral Model Output:
﻿Meeting on Netco Startup

### T5 Model Output:
Organizing an Action Plan for the Start

### Bart Model Output:
Organizing an Action Plan

### Email Body:
﻿Please help summarize the provided email body and generate email subject Of interest - Gas Logistics combined 2001 payroll is $8,209,648.\nThe 2002 Plans were built with a 4.25% combined merit and other which equates to $348,910.\nAt 3.75% the combined merit and other equates to $307,862, a reduction of $41,048.\nOver the next few days, I will be rebuilding the 2002 revised plan for distribution.\nDonna
  
### Reference Output:
"Reduced %",
"gas logistics combined 2001 payroll",
"of interest; new percentage rates coming for revised 2002 distributions of merits",
"plan to rebuild gas logistics payroll plan underway"

### Llama3 Model Output:
﻿Gas Logistics Payroll

### Mistral Model Output:
﻿Gas Logistics combined payroll and merit increase

### T5 Model Output:
Gas Logistics combined 2001 payroll is $8,2

### Bart Model Output:
2002 plans

### Email Body
﻿Please help summarize the provided email body and generate email subject The following reports have been waiting for your approval for more than 4 days. Please review. Owner: James W Reitmeyer Report Name: JReitmeyer 10/24/01 Days In Mgr. Queue: 5

### Reference Ouptut:
reports awaiting approval

### Llama3 Model Output:
﻿Reports Waiting For Approval

### Mistral Model Output:
﻿Approval Needed - Reports Waiting More Than Four Days

### T5 Model Output:
Reports Waiting For Your Approval

### Bart Model Output:
Expense Reports Awaiting Your Approval

### Email Body:
﻿Please help summarize the provided email body and generate email subject A new Kudlow Commentary has been published on Kudlow.com.\nAs a subscriber, you may click the hyperlink below, login, and view the latest commentary.\nAOL Users please note, you may need to copy and paste the hyperlink into your web browser.\nThank You,

### Reference Output:
New Kudlow Commentary

### Llama3 Model Output:
﻿New Kudlow Commentaries Available Online

### Mistral Model Output:
﻿Kudlow Commentary - The New Year's Resolution

### T5 Model Output:
Kudlow Commentary

### Bart Model Output:
Kudlow Commentary

## Model Evaluation Criteria
### Rouge Score
Rouge score measures the similarity between the generated subject and the provided subject using overlapping n-grams. It ranges from 0 to 1, with higher values indicating better summary quality.
## Result
| LLM     	| Rogue1              	| Rogue2               	| RougeL              	| RogueLSum            	|
|---------	|---------------------	|----------------------	|---------------------	|----------------------	|
| Mistral 	| 0.04175057546404236 	| 0.015307029349338995 	| 0.03865576026979294 	| 0.040112317820734385 	|
| Llama3  	| 0.044540652323630435 	| 0.016282087086038018 	| 0.03984053234184394  	| 0.04157418257161926  	|
| T5      	| 0.144567            	| 0.070306             	| 0.140258            	| 0.141119             	|
| Bart    	| 0.267373            	| 0.134597             	| 0.249993            	| 0.250012             	|

## Observations
1. Generative models are very large to be trained on base model, we had to use quantized versions. Also for training we used [PEFT](https://huggingface.co/docs/peft/en/package_reference/lora) 
2. Email subjects generated by both Generative and Seq2Seq Model is contextually correct.
3. Generative models generate word's synonyms, hence Rogue score is very low.
4. Seq2Seq models pick up the words from Email content, which is expected in this experiment, hence Rouge score is high.
5. Bart and T5 both models are encoder-decoder type models, but Bart performs better than T5 due to:
   * Type of corpus these models are trained with is different
   * T5 randomly drop 15% tokens during training, but Bart is trained by corrupting documents and then optimizing a reconstruction loss
   * T5 uses relative positional encoding, where Bart uses absolute positional encoding
   * Bart initializes parameters from N (0, 0.02), where T5 N(0, 1/sqrt(d_model))
     
## HuggingFace Demo URL
**Gradio App:** https://huggingface.co/spaces/GSridhar1982/EmailSubjectGenerationDemo \
Code Files: \
[GradioAppWithModelSelection.ipynb](https://github.com/anukvma/group18_email_subject_generation/blob/main/GradioAppWithModelSelection.ipynb): Gradio App Notebook with model selection option. \
[Group18EmailSubjectGradioApp.ipynb](https://github.com/anukvma/group18_email_subject_generation/blob/main/Group18EmailSubjectGradioApp.ipynb): Gradio App without model selection \

**FAST API:** https://anukvma-emailsubjectapi.hf.space \
Code files: [api(folder)](https://github.com/anukvma/group18_email_subject_generation/tree/main/api): Code for Fast API includes Dockerfile, requirements.txt and main.py \
Curl command for API call:
```
curl --location --request GET 'https://anukvma-emailsubjectapi.hf.space' \
--header 'Content-Type: application/json' \
--data-raw '{
    "model_name":"anukvma/bart-base-medium-email-subject-generation-v5",
    "email_content": "Harry - I got kicked out of the system, so I'\''m sending this from Tom'\''s account. He can fill you in on the potential deal with STEAG. I left my resume on your chair. I'\''ll e-mail a copy when I have my home account running. My contact info is:"
}'
```
