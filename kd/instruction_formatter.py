from typing import Dict, Any

class InstructionFormatter:
    """
    Formats prompt-response pairs into the desired instruction-tuning format.
    """
    def __init__(self, instruction_format: Dict[str, str]):
        self.instruction_field = instruction_format.get("instruction_field", "instruction")
        self.input_field = instruction_format.get("input_field", "input")
        self.output_field = instruction_format.get("output_field", "output")

    def format_record(self, prompt: str, model_response: str) -> Dict[str, Any]:
        """
        Formats a single (prompt, response) pair into a generic instruction format.
        """
        overarching_instruction = (
            "Below is an instruction that describes a task. "
            "Use the provided prompt to understand what needs to be done and provide the best possible response."
        )
        return {
            self.instruction_field: overarching_instruction.strip(),
            self.input_field: prompt.strip(),
            self.output_field: model_response.strip()
        }
