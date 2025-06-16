from io import StringIO

def srt_to_vtt(srt_content: str) -> str:
    input_stream = StringIO(srt_content)
    output_lines = ["WEBVTT\n\n"]

    for line in input_stream:
        line = line.replace(',', '.')  # SRT utilise "," pour les millisecondes
        output_lines.append(line)

    return ''.join(output_lines)
