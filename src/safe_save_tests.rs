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
    let result = write(
        &Config::new(false),
        &mut buffer,
        name.as_os_str().as_bytes(),
        mode,
        false,
        true,
        |_| {},
    );
    let text = match result {
        Ok(n) => format!("ok {n} modified={}\n", buffer.modified),
        Err(error) => format!("error modified={} {}\n", buffer.modified, error.message),
    };
    fs::write(root.join("result"), text).unwrap();
}
