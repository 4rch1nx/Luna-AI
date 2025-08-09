# Luna-AI

An AI chat bot w/TTS, voice recognition, vision and most importantly, personality.

It uses an Ollama based model.

`luna_chat.py`:
Main script
Connects everything together, adds memory and keynotes to the chat.

`luna_prompt.txt`:
Initial prompt to set up personality

`pdf2txt.py`:
Adds custom knowlage
```
python3
>>> import pdf2txt
>>> pdf2txt.pdf_to_text("my_document.pdf", "user_knowledge.txt")
```

`tokens_per_sec.py`:
Run, select model and the script will show you the tokens, gen time and tokens per second to understand the processing power of you GPU.

## TTS
To test TTS, you can run `afplay test.wav`

