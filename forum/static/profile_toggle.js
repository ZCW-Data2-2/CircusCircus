 const target1 = document.getElementById("file_div");
                        const target2 = document.getElementById("email_edit");
                        const target3 = document.getElementById("toggle");
                        const btn = document.getElementById("toggle");
                        btn.onclick = function () {
                            targets = [target1, target2, target3];
                            targets.forEach(function (item, index) {
                                    if (item.style.display !== "none") {
                                        item.style.display = "none";
                                    } else {
                                        item.style.display = "block";
                                    }
                                }
                            )
                        }