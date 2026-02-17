from typing import List, Dict


# def build_structured_prompt(question: str, medicines: list, history: str) -> str:
#
#     structured_context = ""
#
#     for med in medicines:
#         structured_context += f"""
#         Medicine Name: {med.get('medicine_name')}
#         Dosage: {med.get('dosage')}
#         Frequency: {med.get('frequency')}
#         Duration: {med.get('duration')}
#         Purpose: {med.get('purpose')}
#         Common Side Effects: {med.get('common_side_effects')}
#         Warnings: {med.get('warnings')}
#         """
#
#     prompt = f"""
#             You are a licensed medical practitioner explaining medicines to a patient.
#
#             IMPORTANT RULES:
#             - The information below is VERIFIED structured prescription data.
#             - Treat it as trusted medical system data.
#             - Do NOT say "prescription does not mention" if the field is clearly present.
#             - Only say "not specified" if the field is actually empty.
#             - Do not invent additional conditions.
#             - You MUST repeat purpose exactly as provided.
#             - Do NOT infer specific joints or body parts unless explicitly mentioned.
#             - Do NOT narrow or expand the stated indication.
#             - Speak clearly and professionally.
#             - Do not begin with phrases like:
#                 "Certainly", "Hello", "Of course", "I can provide".
#
#
#             Conversation History:
#             {history}
#
#             Verified Prescription Medicine Data:
#             {structured_context}
#
#             Patient Question:
#             {question}
#
#             Answer naturally, professionally, and completely.
#         """
#     return prompt


def build_structured_prompt(question: str, medicines: list, history: str = "") -> str:
    """
    Strict Presentation-Only Mode
    LLM may rephrase but cannot add knowledge.
    """

    structured_data = ""

    for idx, med in enumerate(medicines, start=1):
        structured_data += f"""
                            Medicine {idx}:
                            Name: {med.get("medicine_name", "Not specified")}
                            Dosage: {med.get("dosage", "Not specified")}
                            Frequency: {med.get("frequency", "Not specified")}
                            Duration: {med.get("duration", "Not specified")}
                            Purpose: {med.get("purpose", "Not specified")}
                            Common Side Effects: {med.get("common_side_effects", "Not specified")}
                            Warnings: {med.get("warnings", "Not specified")}
                            -----------------------------------------
                            """

    prompt = f"""
                You are a licensed medical assistant explaining a patient's prescription.
                
                IMPORTANT SYSTEM INSTRUCTIONS:
                
                1. You are NOT allowed to use any medical knowledge outside the structured data below.
                2. You MUST NOT add, infer, expand, or modify medical facts.
                3. If a field says "Not specified", you must clearly state that the prescription data does not provide that information.
                4. You are allowed to:
                   - Rephrase in a clear and professional way
                   - Organize the information nicely
                   - Use a warm but professional tone
                5. Do NOT repeat greetings unnecessarily.
                6. Do NOT say "based on general knowledge".
                7. Do NOT generate new side effects, warnings, or purposes.
                
                Conversation History:
                {history}
                
                Structured Medicine Data:
                {structured_data}
                
                User Question:
                {question}
                
                Now answer using ONLY the structured data above.
                """

    return prompt



def build_rag_prompt(question: str, retrieved_chunks: List[str], history: str) -> str:

    context_text = "\n".join(retrieved_chunks)

    prompt = f"""
    You are assisting a patient regarding their prescription.

    Use ONLY the verified prescription information below.
    Do NOT hallucinate or assume missing details.
    If the answer is not present in the context, clearly state that it is not specified.

    Verified Prescription Context:
    {context_text}

    Previous Conversation:
    {history}

    Patient Question:
    {question}

    Provide a clear, professional, and reassuring answer.
    """

    return prompt
