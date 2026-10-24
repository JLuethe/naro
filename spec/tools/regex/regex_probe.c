/* regex_probe: run POSIX regcomp/regexec exactly as nano does and print the
 * results as JSON lines.  Reference revision 6ed285c3ec7a1d228def4d4e7021c6ba269f620c.
 *
 * Input (stdin), one case per line, fields separated by TAB:
 *   flags  pattern  subject  [start_offset]
 * flags: any of  E (REG_EXTENDED)  I (REG_ICASE)  N (REG_NOSUB)  B (REG_NOTBOL at exec)
 *        S (use REG_STARTEND from start_offset to end, like nano's forward search)
 * Pattern/subject use C escapes \t \n \\ \xHH.
 * Output: {"pattern":..,"subject":..,"flags":..,"compile":0|errcode,"error":"..",
 *          "match":[[so,eo],...]}  (up to 10 groups; -1 for unset)
 * Build: cc -O2 -o regex_probe regex_probe.c      Run under the locale to test (LANG=...).
 */
#include <locale.h>
#include <regex.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static size_t unescape(const char *in, char *out) {
	size_t n = 0;
	while (*in) {
		if (*in == '\\' && in[1]) {
			in++;
			if (*in == 't') { out[n++] = '\t'; in++; }
			else if (*in == 'n') { out[n++] = '\n'; in++; }
			else if (*in == '\\') { out[n++] = '\\'; in++; }
			else if (*in == 'x') { unsigned v; sscanf(in + 1, "%2x", &v); out[n++] = (char)v; in += 3; }
			else { out[n++] = '\\'; }
		} else
			out[n++] = *in++;
	}
	out[n] = '\0';
	return n;
}

static void jstr(const char *s) {
	putchar('"');
	for (; *s; s++) {
		unsigned char c = *s;
		if (c == '"' || c == '\\') printf("\\%c", c);
		else if (c < 0x20 || c >= 0x7f) printf("\\u%04x", c);
		else putchar(c);
	}
	putchar('"');
}

int main(void) {
	char line[8192];
	setlocale(LC_ALL, "");
	while (fgets(line, sizeof line, stdin)) {
		line[strcspn(line, "\n")] = '\0';
		if (!*line || *line == '#') continue;
		char *flags = strtok(line, "\t"), *pat = strtok(NULL, "\t"), *subj = strtok(NULL, "\t"), *st = strtok(NULL, "\t");
		if (!flags || !pat) continue;
		if (!subj) subj = "";
		char P[4096], Sb[4096];
		unescape(pat, P); unescape(subj, Sb);
		int cf = 0, ef = 0, startend = 0;
		if (strchr(flags, 'E')) cf |= REG_EXTENDED;
		if (strchr(flags, 'I')) cf |= REG_ICASE;
		if (strchr(flags, 'N')) cf |= REG_NOSUB;
		if (strchr(flags, 'B')) ef |= REG_NOTBOL;
		if (strchr(flags, 'S')) startend = 1;
		regex_t re;
		int rc = regcomp(&re, P, cf);
		printf("{\"flags\":"); jstr(flags); printf(",\"pattern\":"); jstr(P);
		printf(",\"subject\":"); jstr(Sb);
		if (st) printf(",\"start\":%s", st);
		printf(",\"compile\":%d", rc);
		if (rc) {
			char err[256]; regerror(rc, &re, err, sizeof err);
			printf(",\"error\":"); jstr(err); printf("}\n"); continue;
		}
		regmatch_t m[10];
		if (startend) { m[0].rm_so = st ? atoi(st) : 0; m[0].rm_eo = strlen(Sb); ef |= REG_STARTEND; }
		int er = regexec(&re, Sb, (cf & REG_NOSUB) ? 0 : 10, m, ef);
		printf(",\"exec\":%d", er);
		if (er == 0 && !(cf & REG_NOSUB)) {
			printf(",\"match\":[");
			for (int i = 0; i <= (int)re.re_nsub && i < 10; i++)
				printf("%s[%d,%d]", i ? "," : "", (int)m[i].rm_so, (int)m[i].rm_eo);
			printf("],\"nsub\":%zu", re.re_nsub);
		}
		printf("}\n");
		regfree(&re);
	}
	return 0;
}
