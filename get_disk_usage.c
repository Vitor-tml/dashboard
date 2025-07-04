#include <stdio.h>
#include <sys/statvfs.h>
#include <string.h>
#include <errno.h>
// gcc get_disk_usage.c -o get_disk_usage

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Uso: %s <ponto_de_montagem>\n", argv[0]);
        return 1;
    }
    FILE *file = fopen("disk_output", "a+");
    const char *path = argv[1];
    struct statvfs stats;
    
    if (statvfs(path, &stats) == 0) {
        unsigned long long total_bytes = (unsigned long long)stats.f_blocks * stats.f_bsize;
        unsigned long long free_bytes = (unsigned long long)stats.f_bfree * stats.f_bsize;
        unsigned long long used_bytes = total_bytes - free_bytes;
        
        double percent_used = 0.0;
        if (total_bytes > 0) {
            percent_used = (double)used_bytes / total_bytes * 100.0;
        }
        
        // Imprime os resultados em formato JSON para fácil parsing no Python
        printf("{\"total_bytes\": %llu, \"used_bytes\": %llu, \"free_bytes\": %llu, \"percent_used\": %.2f}\n",
            total_bytes, used_bytes, free_bytes, percent_used);
        if(file != NULL)
        {
            fprintf(file, "particao: %s {\"total_bytes\": %llu, \"used_bytes\": %llu, \"free_bytes\": %llu, \"percent_used\": %.2f}\n",
                argv[1], total_bytes, used_bytes, free_bytes, percent_used);        
        }
    } else {
        // Em caso de erro (ex: permissão negada, caminho inválido), imprime um JSON de erro
        printf("{\"error\": \"Falha ao acessar %s: %s\"}\n", path, strerror(errno));
        return 1; // Retorna 1 para indicar erro
    }
    fclose(file);
    return 0;
}