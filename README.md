# Email Subject Generation (Group 18)

## Description
Generate a succinct subject line from the body of an email.
Email Subject Line Generation task involves identifying the most important sentences in an email and abstracting their message into just a few words. The project provides an opportunity to work with generative models in NLP, specifically using GPT-2 variants, and to explore different metrics for evaluating text generation.

## DataSet
Dataset used is from the below repository for fine tuning the models
The Annotated Enron Subject Line Corpus: https://github.com/ryanzhumich/AESLC

## Models
The following models are fine tuned 
| LLM     	| Framework             | Model Type        | Training Steps       	| Evaluation Method    	| 
|---------	|---------------------	|-------------------|---------------------	|----------------------	|
| Mistral 	| unsloth             	| 4 bit quantized 	| 60 	                  | ROUGE Score         	|
| Llama3  	| unsloth             	| 4 bit quantized 	| 60  	                | ROUGE Score           |
| T5      	| HuggingFace           | Base model       	| 200                  	| ROUGE Score          	|
| Bart    	| HuggingFace           | Base model       	| 200                  	| ROUGE Score          	|

## Training Steps

### Mistral
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
https://huggingface.co/spaces/GSridhar1982/EmailSubjectGenerationDemo
