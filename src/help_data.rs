// GNU nano help introductions, GPL-3.0-or-later.
// Reference 6ed285c3ec7a1d228def4d4e7021c6ba269f620c
use crate::generated::*;
pub const INTROS: &[(u32, &[&str])] = &[
    (
        SEARCH,
        &[
            "Search Command Help Text\n\n Enter the words or characters you would like to search for, and then press Enter.  If there is a match for the text you entered, the screen will be updated to the location of the nearest match for the search string.\n\n The previous search string will be shown in brackets after the search prompt.  Hitting Enter without entering any text will perform the previous search.  ",
            "If you have selected text with the mark and then search to replace, only matches in the selected text will be replaced.\n\n The following function keys are available in Search mode:\n\n",
        ],
    ),
    (
        REPLACEWITH,
        &[
            "=== Replacement ===\n\n Type the characters that should replace what you typed at the previous prompt, and press Enter.\n\n",
            " The following function keys are available at this prompt:\n\n",
        ],
    ),
    (
        GOTO,
        &[
            "Go To Line Help Text\n\n Enter the line number that you wish to go to and hit Enter.  If there are fewer lines of text than the number you entered, you will be brought to the last line of the file.\n\n The following function keys are available in Go To Line mode:\n\n",
        ],
    ),
    (
        INSERT,
        &[
            "Insert File Help Text\n\n Type in the name of a file to be inserted into the current file buffer at the current cursor location.\n\n If you have compiled nano with multiple file buffer support, and enable multiple file buffers with the -F or --multibuffer command line flags, the Meta-F toggle, or a nanorc file, inserting a file will cause it to be loaded into a separate buffer (use Meta-< and > to switch between file buffers).  ",
            "If you need another blank buffer, do not enter any filename, or type in a nonexistent filename at the prompt and press Enter.\n\n The following function keys are available in Insert File mode:\n\n",
        ],
    ),
    (
        WRITE,
        &[
            "Write File Help Text\n\n Type the name that you wish to save the current file as and press Enter to save the file.\n\n If you have selected text with the mark, you will be prompted to save only the selected portion to a separate file.  To reduce the chance of overwriting the current file with just a portion of it, the current filename is not the default in this mode.\n\n The following function keys are available in Write File mode:\n\n",
        ],
    ),
    (
        BROWSER,
        &[
            "File Browser Help Text\n\n The file browser is used to visually browse the directory structure to select a file for reading or writing.  You may use the arrow keys or Page Up/Down to browse through the files, and S or Enter to choose the selected file or enter the selected directory.  To move up one level, select the directory called \"..\" at the top of the file list.\n\n The following function keys are available in the file browser:\n\n",
        ],
    ),
    (
        BSEARCH,
        &[
            "Browser Search Command Help Text\n\n Enter the words or characters you would like to search for, and then press Enter.  If there is a match for the text you entered, the screen will be updated to the location of the nearest match for the search string.\n\n The previous search string will be shown in brackets after the search prompt.  Hitting Enter without entering any text will perform the previous search.\n\n",
            " The following function keys are available at this prompt:\n\n",
        ],
    ),
    (
        BGOTO,
        &[
            "Browser Go To Directory Help Text\n\n Enter the name of the directory you would like to browse to.\n\n If tab completion has not been disabled, you can use the Tab key to (attempt to) automatically complete the directory name.\n\n The following function keys are available in Browser Go To Directory mode:\n\n",
        ],
    ),
    (
        EXEC,
        &[
            "Execute Command Help Text\n\n This mode allows you to insert the output of a command run by the shell into the current buffer (or into a new buffer).  If the command is preceded by '|' (the pipe symbol), the current contents of the buffer (or marked region) will be piped to the command.  ",
            "If you just need another blank buffer, do not enter any command.\n\n You can also pick one of four tools, or cut a large piece of the buffer, or put the editor to sleep.\n\n",
            " The following function keys are available at this prompt:\n\n",
        ],
    ),
    (
        SPELL,
        &[
            "=== Spelling correction ===\n\n The spell checker has examined the spelling of all text in the current buffer or marked region.  An unknown word has been encountered -- it is highlighted and a replacement can now be edited.  After this you will be asked whether to replace each instance of that unknown word.\n\n",
            " The following function keys are available at this prompt:\n\n",
        ],
    ),
    (
        LINTER,
        &[
            "=== Linter ===\n\n In this mode, the status bar shows an error message or warning, and the cursor is put at the corresponding position in the file.  With PageUp and PageDown you can switch to earlier and later messages.\n\n",
            " The following function keys are available in Linter mode:\n\n",
        ],
    ),
    (
        MAIN,
        &[
            "Main nano help text\n\n The nano editor is designed to emulate the functionality and ease-of-use of the UW Pico text editor.  There are four main sections of the editor.  The top line shows the program version, the current filename being edited, and whether or not the file has been modified.  Next is the main editor window showing the file being edited.  The status line is the third line from the bottom and shows important messages.  ",
            "The bottom two lines show the most commonly used shortcuts in the editor.\n\n Shortcuts are written as follows: Control-key sequences are notated with a '^' and can be entered either by using the Ctrl key or pressing the Esc key twice.  Meta-key sequences are notated with 'M-' and can be entered using either the Alt, Cmd, or Esc key, depending on your keyboard setup.  ",
            "Also, pressing Esc twice and then typing a three-digit decimal number from 000 to 255 will enter the character with the corresponding value.  The following keystrokes are available in the main editor window.  Alternative keys are shown in parentheses:\n\n",
        ],
    ),
];
