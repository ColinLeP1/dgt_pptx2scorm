def srt_to_vtt(srt_path, vtt_path):
    with open(srt_path, 'r', encoding='utf-8') as srt_file:
        lines = srt_file.readlines()

    with open(vtt_path, 'w', encoding='utf-8') as vtt_file:
        vtt_file.write("WEBVTT\n\n")  # entête obligatoire VTT

        for line in lines:
            if '-->' in line:
                line = line.replace(',', '.')
            vtt_file.write(line)
