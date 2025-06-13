def vtt_to_srt(vtt_path, srt_path):
    with open(vtt_path, 'r', encoding='utf-8') as vtt_file:
        lines = vtt_file.readlines()

    with open(srt_path, 'w', encoding='utf-8') as srt_file:
        for line in lines:
            # Ignorer la ligne "WEBVTT" et les lignes vides en début de fichier
            if line.strip() == "WEBVTT" or line.strip() == "":
                continue
            
            # Si la ligne contient une flèche, remplacer '.' par ',' dans les timestamps
            if '-->' in line:
                line = line.replace('.', ',')
            
            srt_file.write(line)
