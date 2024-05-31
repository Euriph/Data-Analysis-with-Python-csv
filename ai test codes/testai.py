import openai

openai.api_key = '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'

completion = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "user",
            "content": "How do I output all files in a directory using Python?",
        },
    ],
)
print(completion.choices[0].message.content)
