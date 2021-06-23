# WRPI AUTO

The broadcast automation system for WRPI or any general broadcast station. Features include:

- Automated station ID
- Programmable show schedule
- Loudness normalization (EBU R 128)
- Configuration hot reload
- Text user interface and headless mode
- Station logging
- Email/Discord alert

```text
                   WRPI Broadcast Automation System Jun-23-2021 02:28:53             
+-- Media Queue (9) ---------+  +-- Station Log ---------------------------------------------+  
|   1. [0:08:16] lib\show\Bo |  | 2021-06-23 02:22:14,252 - Daemon     [INFO] Scheduler star |  
|   2. [0:03:44] lib\show\Le |  | 2021-06-23 02:22:14,252 - TUI        [INFO] TUI starting.. |  
|   3. [0:02:22] lib\show\My |  | 2021-06-23 02:22:18,091 - TUI        [INFO] Playing "lib\s |  
|   4. [0:04:37] lib\show\O  |  | 2021-06-23 02:24:15,003 - Daemon     [WARNING] RAM usage t |  
|   5. [0:03:02] lib\show\So |  | 2021-06-23 02:26:30,000 - Daemon     [INFO] Mixer digest:  |  
|   6. [0:04:13] lib\show\WR |  |                                                            |  
|   7. [0:06:37] lib\show\wr |  |                                                            |  
|   8. [0:05:40] lib\show\WR |  |                                                            |  
|   9. [0:01:08] lib\show\WR |  |                                                            |  
|                            |  |                                                            |  
|                            |  |                                                            |  
|                            |  |                                                            |  
+----------------------------+  |                                                            |  
+-- Now Playing -------------+  |                                                            |  
| [ show ] (100%) lib\show\B |  |                                                            |  
| [ fill ] (100%) <empty>    |  |                                                            |  
| [ PSA  ] (100%) <empty>    |  |                                                            |  
|                            |  |                                                            |  
+----------------------------+  |                                                            |  
+-- System Statitics --------+  |                                                            |  
| [ CPU ] (  9%)             |  |                                                            |  
| [ RAM ] ( 94%) free:    0. |  |                                                            |  
| [ STR ] ( 38%) free:  315. |  |                                                            |  
| [ PWR ] (100%)             |  |                                                            |  
+----------------------------+  +------------------------------------------------------------+ 
[M]ute [P]ause [CTRL]+[UP/DN]Volume [H]elp [Q]uit - Use arrow keys to navigate. ENTER to focus. 
```  

## Deployment

Refer to [deployment](doc/manual/user.md#Deployment) section in `doc/manual/user.md`.

## Documentation

Checkout user manual and programming manual in `doc/` folder.

