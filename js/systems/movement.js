window.G = window.G || {};

G.Movement = Object.freeze({
  updatePlayer(player, dt) {
    const [axisX, axisY] = G.Input.axis();
    const wantsMove = axisX !== 0 || axisY !== 0;
    const running = G.Input.isHeld('shiftleft', 'shiftright');
    const creepFast = !G.Input.isHeld('controlleft', 'controlright');

    if (!player.canMove()) {
      player.moving = false;
      return;
    }

    let moved = false;
    if (wantsMove) {
      player.direction = G.directionFromVector(axisX, axisY, player.direction);
      const speed = player.speed * dt;
      const dx = axisX * speed;
      const dy = axisY * speed;

      if (G.MapWorld) {
        moved = G.MapWorld.movePoint(player, dx, dy);
      } else {
        player.x += dx;
        player.y += dy;
        moved = true;
      }
    }

    player.moving = wantsMove && moved;
    player.state.setLocomotion({ moving: player.moving, running, creepFast });
  }
});
