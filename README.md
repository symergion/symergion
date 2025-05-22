# SymErgion

## Abstract
A human and artificial entities forming collective intellegence to contribute to a shared purpose. The concept implements the idea of a human at the core, augmented by intellectual systems, while maintaining control over and synergy with AI, and evolving through core and periphery self-learning guided by human priorities (see [manifesto](augmented_human_manifesto.pdf)).

## Proof of Concept
This version of SymErgion represents proof of concept of the augmented human concept.

### Definitions
Definitions of introduced terms.

#### Augmented Human
An autonomous collective of collaborating intellectual systems with a human at its core. Human in the core is a unique individual and holds exclusive absolute local control over personal modifications of the systems’ code and the weights of machine learning models.

#### SymErgion
Implementation of the Augmented Human periphery.

#### SLM
A Large Language Model capable of running on personal hardware.

#### SymErg
A locally running SLM-based artificial entity.

#### Ergon
A particular task that the Augmented Human works on.

### PoC Scope
The goal of the PoC is to prove that the Augmented Human concept can be implemented using personal computational hardware. Due to the main limiting factor being the scarcity of GPU resources, the primary open question is whether it is possbile to allocate enough GPU compute for local model tuning. Based on this, the goal is to reduce its usage on inference.

The PoC framefork allows collaboration between the Augmented Human core and Augmented Human periphery, utilizing CPU computational resources for inference in a manner that enables achieving the goals.

1. Given that models runing on CPU are several orders of magnitude slower compared to GPU, the collaboration framework should be convinient for long response times. Collaboration within a development team seems like a good match.
2. Given that only very small SLMs are capable of responding reasonably quickly, it should be arranged as colaboration between the human in the role of a team member with senior expertise and the Augmented Human periphery entities in the role of a team member with junior expertise.
3. Considering a slight rephrasing of Occam's principle, interfaces should not be multiplied beyond necessity.

Having all that in mind, we have the PoC that does the following on startup:
- Instantiates SymErgion watching local git repository handler, catching repository branches and commits notes related events.
- Instantiates one or a few SymErgs, watching updates from SymErgion.
- If the repository already contains an Ergon and related SymErg branches and their annotations, it syncs the SymErgion state with the repository.

The PoC implements the following workflow of Human-SymErgion colaboration:
1. Initial generation:
	* Human creates a feature branch and specifies the task parameters by annotating branched commit.
	* SymErgion instantiates Ergon with parameters acquired from the branch name and assigns SymErgs to it.
	* SymErgion calls Ergon to update its prompt based on the note message.
	* SymErgion updates SymErgs with the prompt.
	* For each SymErg:
		* SymErg generates a response.
		* SymErg updates Ergon with the response.
		* Ergon creates Ergon-related SymErg branch and commits into it.
2. Review committed code and provide feedback:
	* If no response is good enough. Human selects the best one and annotates its branch with concise notes describing the specific changes required to meet the requirements as if a junior specialist were being instructed.
	* SymErgion updates Ergon's prompt with the note message.
	* SymErgion updates SymErgs with updated prompt.
	* For each SymErg:
		* SymErg generates a response.
		* SymErg updates Ergon with the response.
		* Ergon commits into Ergon-related SymErg branch.
3. Revoke last feedback:
	* If the addressed feedback has not improved the situation. Human deletes the note containing the feedback.
	* SymErgion removes the deleted note message from the Ergon prompt.
	* SymErgion updates SymErgs with the updated prompt.
	* For each SymErg:
		* SymErg generates a response (uses a cached one if it was generated during the current session).
		* SymErg updates Ergon with the response.
		* Ergon commits into the Ergon-related SymErg branch with a commit message starting with "Revert:" and containing reverted prompt.
Steps 2 and 3 (if necessary) should be repeated untill a satisfactory result is achieved.
4. If last changes could be made faster than describing them in a note, they could be done and commited manually. Please note that requesting SymErgion to make changes after you have commited manual change will overwrite your code with generated code.
5. After Human merges SymErg branch into the master branch and deletes feature branch, the process ends.

### Deployment

#### Build Docker Image
To deploy Symergion, get the Linux docker image of your preference, having git, Python>=3.10.13, PyTorch>=2.2.1, Transformers>=4.50.3 installed and pass it as a `docker build` command argument running in your symergion directory:
```bash
docker build --build-arg BASE_CONTAINER="image-of-your-preference" -t symergion:latest .
```

#### Configure Settings
Store SymErgion settings in a JSON configuration file located in the directory where LLMs checkpoints are saved.

Example of config settings (specific SLMs are selected for illustration purposes):
```json
{
  "idle_cores": 4,
  "cache_size": 1,
  "response_cache_size": 100,
  "ntokens": 128,
  "default_branch": "main",
  "task_branch_spec": "task_branch:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)",
  "checkpoints": [
    {
      "name_or_path": "Qwen2.5-Coder-7B",
      "trait": "coding"
    },
    {
      "name_or_path": "granite-3.1-3b-a800m-base",
      "trait": "coding"
    }
    {
      "name_or_path": "granite-3.2-2b-instruct",
      "trait": "reasoning",
      "reasoning_start_tokens": [
        10921,
        438,
        1672,
        10889,
        2164,
        44,
        203
      ],
      "reasoning_stop_tokens": [
        203,
        10921
      ]
    }
  ],
  "templates": {
    "TestCase": {
      "params": {
        "source": "source:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)(?:[,;]?[\\s]*|[\\n]?)",
        "destination": "destination:[\\s]*([\\p{L}\\p{N}_\\-\\.\\/]+)(?:[,;]?[\\s]*|[\\n]?)"
      },
      "call_to_action": "Create unittest TestCase",
      "code_starter": "import unittest\n"
    }
  }
}
```

Here:
##### `idle_cores`
Specifies the quantity of CPU cores that will not be allocated to Pytorch threads. It should be set based on balancing CPU resource needs for other tasks, your CPU tolerance to overheating and expected generation speed.

##### `cache_size`
Specifies the number of SLMs to be cached.

##### `response_cache_size`
Specifies the number of SLMs' responces to be cached.

##### `ntokens`
Is a parameter used to calculate `max_new_tokens` for generation based on the model's `max_position_embeddings`:
```python
max_new_tokens = max_position_embeddings - (max_position_embeddings - ntokens) * math.exp(-encodings_len / (max_position_embeddings - ntokens))
```

##### `default_branch`
Is the name of the Git repository's default branch.

##### `task_branch_spec`
Is the task branch name specification.

##### `checkpoints`
Is a list of SLMs checkpoints to be used.

###### `name_or_path`
Is the particular model checkpoint path within the models directory.

###### `trait`
Specifies in which role the model should be used: "coding" or "reasoning"

###### `reasoning_start_tokens`
Specifies the sequence of tokens marking the start of the reasoning section (applies only to the "reasoning" trait)

###### `reasoning_stop_tokens`
Specifies the sequence of tokens marking the end of the reasoning section (applies only to the "reasoning" trait)

##### `templates`
Supported Ergon types templates. Current includes only "TestCase".

###### `params`
Specifies the format used to define source and destination file names in notes.

###### `call_to_action`
Is the call-to-action part of the initial prompt.

###### `code_starter`
Starting part of code to be generated.

#### Run
Run the built container:
```bash
docker run --rm -itd -v /path/to/llms/:/models -v /path/to/local/repository:/repo --name symergion symergion:latest
```

Attach the running container:
```bash
docker attach symergion
```

Input symergion config file, i.e., `short_code_symergs.json` containing the configuration from the above sample.

Once SymErgion is up and running, you will see `Observing /repo/.git/logs/refs`

### Usage examples
Let's have a look at one example of working with the copy of SymErgion repository.

#### Create Ergon Branch
Creation of a feature branch for the `capture_output` utility unittest generation.

Based on our configuration file, the branch prefix should be `TestCase`, so the feature branch has been created accordingly:
```bash
git branch TestCase_capture_output
```

#### Annotate Ergon Branch with Initial Note
Annotation of the `TestCase_capture_output` branch with an initial note. Based on our configuration file, this should be:
```bash
git notes add -m "task_branch: TestCase_capture_output, source: utils/capture_output.py, destination: test_capture_output.py"
```
It has been seen that model `granite-3.2-2b-instruct` was loaded and generated reasoning based on the cooked prompt. Note that the cooked prompt is enriched with the code from the source and destination (if exists) files. In my case, it took `granite-3.2-2b-instruct` 75.3s to generate 280 new tokens. The reasoning part was used to enrich the prompt.

Than it has been seen that models `Qwen2.5-Coder-7B` and `granite-3.1-3b-a800m-base` are being loaded and started generating responses for the given enriched prompt.
It took `Qwen2.5-Coder-7B` 66.3s to generate 63 new tokens and it took `granite-3.1-3b-a800m-base` 119.7s to generate 681 new tokens.

#### Review Results
Once generation is completed it has been seen that SymErg branches `Qwen2.5-Coder-7B_TestCase_capture_output` and `granite-3.1-3b-a800m-base_TestCase_capture_output` were created by SymErgion.

The review of the results for the both models, starts with prompts cooked and enriched with the reasoning part. The commit messages contain the prompts (excluding the code of source and target files), so they can be easily addressed like this:
```bash
git log TestCase_capture_output..Qwen2.5-Coder-7B_TestCase_capture_output
git log TestCase_capture_output..granite-3.1-3b-a800m-base_TestCase_capture_output
```
Note that the reasoning part is not mandatory; it could be avoided by not speciyfing any model with the reasoning trait in the configuration.

Review of the generated code:
```bash
git diff TestCase_capture_output..Qwen2.5-Coder-7B_TestCase_capture_output
git diff TestCase_capture_output..granite-3.1-3b-a800m-base_TestCase_capture_output
```

It looked like the `Qwen2.5-Coder-7B` result was closer to what is required.

#### Provide Feedback
Pointing of SymErgs attention to the use of `setUp` method as a best practice:
```bash
git notes add -m "Use setUp method" Qwen2.5-Coder-7B_TestCase_capture_output
```

It has been seen that SymErgion started loadng coding models and generating code for the updated prompt.
It took `Qwen2.5-Coder-7B` 99.7s to generate 81 new tokens and it took `granite-3.1-3b-a800m-base` 168.0s to generate 686 new tokens.

#### Verify the Results
Verification of the prompt:
```bash
git log TestCase_capture_output..Qwen2.5-Coder-7B_TestCase_capture_output
git log TestCase_capture_output..granite-3.1-3b-a800m-base_TestCase_capture_output
```
It has been seen that new commits have the notes with last feedback as commit messages. Please note that when generating the response, they all combine into one prompt.

Verification of the generated code:
```bash
git diff TestCase_capture_output..Qwen2.5-Coder-7B_TestCase_capture_output
git diff TestCase_capture_output..granite-3.1-3b-a800m-base_TestCase_capture_output
```
It has been seen that `setUp` method was used, but not in the expected way.

#### Revoke the Last Feedback Notes
Revoking of the last feedback.
```bash
git notes
git notes show f3f27311c19af99fd5aa9260305ef8961271a439
git notes remove f3f27311c19af99fd5aa9260305ef8961271a439
```

Please note that second and third commands are dependent on the result of the first command.

It has been seen that SymErgs responces use cached results.

#### Verify the Results
Verification of the commits:
```bash
git log TestCase_capture_output..Qwen2.5-Coder-7B_TestCase_capture_output
git log TestCase_capture_output..granite-3.1-3b-a800m-base_TestCase_capture_output
```
It has been seen that a new commit "Revert: Use setUp method" appeared in both branches.

Verification of the code:
```bash
git diff TestCase_capture_output..Qwen2.5-Coder-7B_TestCase_capture_output
git diff TestCase_capture_output..granite-3.1-3b-a800m-base_TestCase_capture_output
```
It has been seen that the cached generated code reappeared.

#### Provide more specific feedback
Pointing of SymErgs attention to the use of `setUp` method as a best practice in a more specific manner:
```bash
git notes add -m "Use setUp for specifying function producing output to be caught" Qwen2.5-Coder-7B_TestCase_capture_output
```

It has been seen that SymErgion starts loadng coding models and generating code for the updated prompt.

It took `Qwen2.5-Coder-7B` 220.6s to generate 282 new tokens and it took `granite-3.1-3b-a800m-base` 171.7s to generate 643 new tokens.

#### Verify the Results
Verification of the prompt:
```bash
git log TestCase_capture_output..Qwen2.5-Coder-7B_TestCase_capture_output
git log TestCase_capture_output..granite-3.1-3b-a800m-base_TestCase_capture_output
```
It has been seen that new commits have the notes with the last feedback as commit messages. Please note that when generating the response, they all combine into one prompt.

Verification of the generated code:
```bash
git diff TestCase_capture_output..Qwen2.5-Coder-7B_TestCase_capture_output
git diff TestCase_capture_output..granite-3.1-3b-a800m-base_TestCase_capture_output
```
It has been seen that `setUp` method is used in the expected way.

#### Last Changes
`Qwen2.5-Coder-7B` repeated tested function code. Feedback to SymErgion could be provided or unnecessary code lines could be deleted manually. Considering that deleting is faster than writing feedback, it makes sense to do the last changes manually.

### Overall remarks
It is a good practice to maintain several configuration files with different sets of SLMs, based on your experience of which SLM shows better results for specific codebases. Enriching the prompt using reasoning model(s) could improve overall quality with less compute, though it is not the case for all sorts of tasks. Note ithat you can assign more than one reasoner to specific configurations. In that case, they will produce reasoning parts independently and the prompt will be enriched with all of them combined.

Two to three SymErgs might be a good mix. Running more models will unnecessarily increase the completion time and ammount of consumed computing resources. Running solo model would make your SymErgion more susceptible to weak areas within a single model, as different models have different strengths and weaknesses.

Do not use `git reset` for SymErg branches, SymErgions' workflow doesn't support consistent work with inconsistent SymErg branches.

## License Agreement
SymErgion is licensed under MIT License. You van find the license file under the SymErgion repository.

## Contacts
If you are interested to leave message you could find contact in https://t.me/symergion channel description.

## Citation
If you find this work helpfull, feel free to give it a cite.
```
@misc{SymErgion,
	title={SymErgion},
	author={Aleksei Mitin},
	year={2025},
	url={https://t.me/symergion},
}
```

## Classes

* Observer():
	* Any observer implementation should derive from this class.
	* Abstract Methods:
		* update()
* Handler():
	* Any handler implementation should derive from this class
	* Attributes:
		* symergion
	* Abstract Methods:
		* dispatch()
		* sync_state()
* HandlerCoding(Handler):
	* Attributes:
		* local_branches
		* remote_branches
		* local_notes
		* remote_notes
	* Private Attributes:
		* _handled
	* Methods:
		* dispatch()
		* sync_state()
	* Private Methods:
		* _check_for_branches()
		* _get_branches_diff()
		* _check_for_notes()
		* _process_note()
* SymErgion(Observer):
	* Any symergion implementation should derive from this class.
	* Attributes:
		* symergs
		* ergons
	* Methods:
		* attach_symerg()
		* detach_symerg()
	* Abstract Methods:
		* update()
		* instantiate_symerg()
		* instantiate_ergon()
		* decomission_ergon()
	* Private Abstract Methods:
		* _notify()
* SymErgionCoding(SymErgion):
	* Attributes:
		* task_branch_spec
		* checkpoints
		* feature_names_pattern
		* supported_coders
		* supported_tasks
		* repo
		* branches
		* ergon_branches
		* feature_names
		* notes
		* ergon_notes
		* coders
		* reasoners
	* Private Attributes:
		* _templates
		* _config
	* Methods:
		* update()
		* instantiate_symerg()
		* instantiate_ergon()
		* decomission_ergon()
	* Private Methods:
		* _extract_feature_name()
		* _get_not_handled_coders()
		* _notify()
		* _new_feature_branch()
		* _delete_feature_branch()
		* _new_model_branch()
		* _delete_model_branch()
		* _add_note()
		* _remove_note()
		* _update_with_payload
		* _update_with_no_payload()
* SymErg(Observer):
	* Any symerg implementation should derive from this class.
	* Attributes:
		* name_or_path
		* ergons
		* model
		* tokenizer
		* trait
	* Private Attributes:
		* _checkpoint
		* _cache_size
		* _response_cache_size
		* _ntokens
	* Methods:
		* get_model()
		* get_tokenizer()
		* attach_ergon()
		* detach_ergon()
		* get_max_new_tokens()
		* get_model()
		* get_tokenizer()
	* Private Methods:
		* __getattr__()
		* _notify()
	* Abstract Methods:
		* update()
* SymErgCoder(SymErg):
	* Methods:
		* update()
		* generate()
	* Private Methods:
		* _notify()
* SymErgReasoner(SymErg):
	* Private Attributes:
		* reasoning_start_tokens
		* start_tokens_len
		* reasoning_end_tokens
		* end_tokens_len
	* Methods:
		* update()
		* generate()
	* Private Methods:
		* _notify()
* Ergon(Observer):
	* Any ergon implementation should derive from this class.
	* Attributes:
		* name
	* Abstract Methods:
		* update()
* ErgonCode(Ergon):
	* Attributes:
		* template
		* params
		* repo
		* task_type
		* branches
		* reasoners
		* notes
		* source_file
		* destination_file
		* source_file
		* prompt
		* initial_message
	* Methods:
		* get_symerg_messages()
		* update()
		* checkout()
		* respond()
* Prompt(list):
	* Class Attributes:
		* patterns
	* Attributes:
		* template
		* params
		* prefix
		* initial_prompt
		* body
		* suffix
		* comments
	* Private Attributes:
		* _for_entity
	* Methods:
		* format_reasoning()
	* Private Methods:
		* __str__()
* Config()
	* Class Methods:
		* from_json()
	* Private Methods:
		* __getattr__()
* Repo():
	* Attributes:
		* remote
		* local
		* branch_pattern
		* default_branch
		* current_branch
		* remote_branches
		* notes
	* Class Methods:
		* run_command()
	* Methods:
		* get_note_branches()
		* get_note_message()
		* get_object()
		* object_exists()
		* get_object_branches()
		* get_timestamp()
		* get_ergon_branch_messages()
		* get_objects_messages()
		* create_branch()
		* delete_branch()
		* delete_remote_branch()
		* checkout()
		* add()
		* commit()
		* set_user()
	* Private Methods:
		* _pull()
		* _push()
		* _prune_remote()
		* _prune_remote_notes()
* Branches(list):
	* Attributes:
		* feature_branch
		* remotes
		* coders
		* repo
	* Methods:
		* append()
		* remove()
		* clear()
* CustomList(list):
	* Private Methods:
		* __contains__()
		* __sub__()

