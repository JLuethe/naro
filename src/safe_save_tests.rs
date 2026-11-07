//! Subprocess entry for tests/safe-save/run.py. Paths belong to its fixture.
use super::*;

#[test]
#[ignore = "requires the owned fixture from tests/safe-save/run.py"]
fn fixture_save() {
    let root = std::env::var_os("NARO_SAVE_FIXTURE").expect("safe-save fixture is required");
    let root = PathBuf::from(root);
    let collision = std::env::var_os("NARO_SAVE_COLLISION").is_some();
    let name = root.join(if collision {
        format!("data/.naro-save-{}-0", std::process::id())
    } else {
        "data/target".to_string()
    });
    fs::write(root.join("destination"), name.as_os_str().as_bytes()).unwrap();
    let mut buffer = Buffer::new(
        name.as_os_str().as_bytes().to_vec(),
        vec![b"replacement".to_vec(), vec![]],
    );
    buffer.modified = true;
    let mode = std::env::var("NARO_SAVE_MODE").unwrap().parse().unwrap();
    let backup = std::env::var_os("NARO_SAVE_BACKUP").is_some();
    let mut config = Config::new(false);
    config.set(MAKE_BACKUP, backup);
    if let Some(directory) = std::env::var_os("NARO_SAVE_BACKUP_DIR") {
        config.strings.insert(
            "backupdir".into(),
            directory.as_os_str().as_bytes().to_vec(),
        );
    }
    config.set(
        INSECURE_BACKUP,
        std::env::var_os("NARO_SAVE_INSECURE").is_some(),
    );
    if std::env::var_os("NARO_SAVE_CONFINED").is_some() {
        config
            .strings
            .insert("operatingdir".into(), root.as_os_str().as_bytes().to_vec());
        config.operating_root = Some(File::open(&root).unwrap());
    }
    if std::env::var_os("NARO_SAVE_BACKUP_COLLISION").is_some() {
        let collision = root.join(format!("data/.naro-backup-{}-0", std::process::id()));
        let seed = root.join("collision-seed");
        fs::write(&seed, b"unrelated collision").unwrap();
        fs::hard_link(seed, &collision).unwrap();
        fs::write(
            root.join("backup-collision"),
            collision.as_os_str().as_bytes(),
        )
        .unwrap();
    }
    let mut progress = Vec::new();
    let result = write(
        &config,
        &mut buffer,
        name.as_os_str().as_bytes(),
        mode,
        false,
        !backup,
        |stage| {
            progress.push(match stage {
                WriteProgress::Status(s) | WriteProgress::Warning(s) => s.to_owned(),
            })
        },
    );
    fs::write(root.join("progress"), progress.join("\n")).unwrap();
    let text = match result {
        Ok(n) => format!("ok {n} modified={}\n", buffer.modified),
        Err(error) => format!(
            "error modified={} confirm_backup={} {}\n",
            buffer.modified, error.confirm_backup, error.message
        ),
    };
    fs::write(root.join("result"), text).unwrap();
}
