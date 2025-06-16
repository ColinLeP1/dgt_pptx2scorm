from io import StringIO

def vtt_to_srt(vtt_content: str) -> str:
    input_stream = StringIO(vtt_content)
    output_lines = []

    for line in input_stream:
        if line.startswith("WEBVTT"):
            continue
        line = line.replace('.', ',')  # VTT utilise "." pour les millisecondes
        output_lines.append(line)

    return ''.join(output_lines)
