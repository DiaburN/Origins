window.G = window.G || {};

G.Movement = Object.freeze({
  updatePlayer(player, dt) {
    const [axisX, axisY] = G.Input.axis();
    const moving = axisX !== 0 || axisY !== 0;
    const running = G.Input.isHeld('shiftleft', 'shiftright');
    const creepFast = !G.Input.isHeld('controlleft', 'controlright');

    if (!player.canMove()) {
      player.moving = false;
      return;
    }

    if (moving) {
      player.direction = G.directionFromVector(axisX, axisY, player.direction);
      player.x += axisX * player.speed * dt;
      player.y += axisY * player.speed * dt;
    }

    player.moving = moving;
    player.state.setLocomotion({ moving, running, creepFast });
  }
});
